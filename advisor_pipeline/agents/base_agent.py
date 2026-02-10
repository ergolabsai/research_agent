from abc import ABC, abstractmethod
from typing import Any, Dict, Type, TypeVar
from pydantic import BaseModel
import instructor
from anthropic import Anthropic
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool

from advisor_pipeline.config.settings import settings

T = TypeVar('T', bound=BaseModel)


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
            model=settings.model_name,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            api_key=settings.anthropic_api_key
        )
        
        # Tools will be defined by child classes
        self.tools: list[BaseTool] = []
        
        # Agent executor will be initialized after tools are set
        self.agent_executor: AgentExecutor | None = None
    
    def initialize_agent(self, prompt: ChatPromptTemplate):
        """Initialize the LangChain agent with tools and prompt."""
        if not self.tools:
            raise ValueError(f"No tools defined for agent {self.name}")
        
        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10
        )
    
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
