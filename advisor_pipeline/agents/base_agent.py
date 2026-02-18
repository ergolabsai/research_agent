from abc import ABC, abstractmethod
from typing import Any, Dict, Type, TypeVar, Annotated
from pydantic import BaseModel
import instructor
from anthropic import Anthropic
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import BaseTool
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict

from advisor_pipeline.config.settings import settings

T = TypeVar('T', bound=BaseModel)


class AgentState(TypedDict):
    """State for LangGraph agent."""
    messages: Annotated[list[BaseMessage], add_messages]


class BaseAgent(ABC):
    """Base class for all specialized agents in the pipeline."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

        # Initialize Anthropic client with Instructor for structured outputs
        self.client = instructor.from_anthropic(
            Anthropic(api_key=settings.anthropic_api_key)
        )

        # Initialize LangChain LLM for agent orchestration
        self.llm = ChatAnthropic(
            model_name=settings.model_name,
            temperature=settings.temperature,
            max_tokens_to_sample=settings.max_tokens,
            api_key=settings.anthropic_api_key,
            timeout=settings.timeout_seconds,
            stop=None
        )

        # Tools will be defined by child classes
        self.tools: list[BaseTool] = []

        # Agent graph will be initialized after tools are set (only for agents with tools)
        self.agent_graph = None

        self.system_prompt = """You are a scientist reviewing a new paper.  Your job is to:
1. Identify the paper's main claim or thesis
2. Break down the argument into discrete logical steps
3. Identify dependencies between steps (which steps build on which)
4. Note which section each step appears in

Be precise and capture the logical flow of the argument, not just a summary.

You're job is also to remain highly skeptical of the author's conclusions.
You are looking for mistakes in logic and you should not assume their results are conclusive."""

    def initialize_agent(self):
        """Initialize the LangGraph agent with tools.

        Only builds a graph when the agent has tools (for the agent<->tools loop).
        Toolless agents should use invoke_llm() instead.
        """
        self.tools = self.get_tools()

        if not self.tools:
            # No tools — no graph needed. Use invoke_llm() for direct calls.
            return

        # Bind tools to LLM
        bound_llm = self.llm.bind_tools(self.tools)

        # Define the agent node
        def call_model(state: AgentState):
            messages = state["messages"]
            if not messages or not hasattr(messages[0], "content") or "system" not in str(type(messages[0])):
                messages = [{"role": "system", "content": self.system_prompt}] + messages
            response = bound_llm.invoke(messages)
            return {"messages": [response]}

        # Build the graph with agent <-> tools loop
        workflow = StateGraph(AgentState)
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", ToolNode(self.tools))
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", tools_condition)
        workflow.add_edge("tools", "agent")

        self.agent_graph = workflow.compile()

    def invoke_llm(self, input_text: str) -> str:
        """Call the LLM directly without LangGraph overhead.

        Use this for agents that have no tools. The system prompt is
        prepended automatically.

        Args:
            input_text: The input to send to the LLM

        Returns:
            The LLM's response as a string
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            HumanMessage(content=input_text),
        ]
        response = self.llm.invoke(messages)
        if hasattr(response, "content"):
            return response.content
        return str(response)

    def invoke_agent(self, input_text: str) -> str:
        """Invoke the LangGraph agent with tools.

        Only works for agents that have tools and have called initialize_agent().
        Toolless agents should use invoke_llm() instead.

        Args:
            input_text: The input to send to the agent

        Returns:
            The agent's final response as a string
        """
        if not self.agent_graph:
            raise ValueError(f"Agent graph not initialized for {self.name}")

        result = self.agent_graph.invoke(
            {"messages": [HumanMessage(content=input_text)]},
            {"recursion_limit": 10}
        )

        # Extract the final message
        if result and "messages" in result:
            final_message = result["messages"][-1]
            if hasattr(final_message, "content"):
                return final_message.content
            return str(final_message)
        return ""

    def invoke_agent_with_vision(self, input_text: str, media_type: str, image_data: str) -> str:
        """
        Send an image plus text prompt to Claude's vision API, then pass
        the result through the LangGraph agent for formatting.

        Args:
            input_text: The text prompt to accompany the image
            media_type: MIME type of the image (e.g. 'image/png')
            image_data: Base64-encoded image data

        Returns:
            The agent's formatted response as a string
        """
        client = Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model=settings.model_name,
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {"type": "base64", "media_type": media_type, "data": image_data},
                        },
                        {
                            "type": "text",
                            "text": input_text,
                        },
                    ],
                }
            ],
        )
        return response.content[0].text

    def get_structured_output(
        self,
        prompt: str,
        response_model: Type[T],
        context: Dict[str, Any] | None = None
    ) -> T:
        """
        Use Instructor to get guaranteed structured output.
        
        Args:
            prompt: The prompt to send to the LLM
            response_model: Pydantic model class to enforce
            context: Optional context dictionary to include in prompt
            
        Returns:
            Validated instance of response_model
        """
        messages = []
        
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            messages.append({
                "role": "user",
                "content": f"Context:\n{context_str}\n\n{prompt}"
            })
        else:
            messages.append({"role": "user", "content": prompt})
        
        response = self.client.messages.create(
            model=settings.model_name,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
            messages=messages,
            response_model=response_model
        )
        
        return response
    
    @abstractmethod
    def run(self, input_data: Dict[str, Any]) -> BaseModel:
        """
        Execute the agent's main task.
        
        Args:
            input_data: Dictionary containing all necessary input
            
        Returns:
            Pydantic model with results
        """
        pass
    
    @abstractmethod
    def get_tools(self) -> list[BaseTool]:
        """Return list of tools this agent needs."""
        pass
