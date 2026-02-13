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

        # Agent graph will be initialized after tools are set
        self.agent_graph = None

        self.system_prompt = ""

    def initialize_agent(self, system_prompt: str):
        """Initialize the LangGraph agent with tools and system prompt."""
        if not self.tools:
            raise ValueError(f"No tools defined for agent {self.name}")

        # Bind tools to the LLM
        llm_with_tools = self.llm.bind_tools(self.tools)

        # Store system prompt
        self.system_prompt = system_prompt

        # Define the agent node
        def call_model(state: AgentState):
            messages = state["messages"]
            # Prepend system message if not already there
            if not messages or not hasattr(messages[0], "content") or "system" not in str(type(messages[0])):
                messages = [{"role": "system", "content": self.system_prompt}] + messages
            response = llm_with_tools.invoke(messages)
            return {"messages": [response]}

        # Build the graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", ToolNode(self.tools))

        # Add edges
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", tools_condition)
        workflow.add_edge("tools", "agent")

        # Compile the graph
        self.agent_graph = workflow.compile()

    def invoke_agent(self, input_text: str) -> str:
        """
        Invoke the LangGraph agent with input text.

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
