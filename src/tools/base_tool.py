"""Base tool class for all restaurant reservation tools."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseTool(ABC):
    """Abstract base class for all tools."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name for function calling."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for the LLM."""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """JSON Schema for tool parameters."""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with given parameters.
        
        Returns:
            Dictionary with success status and result data
        """
        pass
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """Get tool definition for Groq function calling."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
    
    def validate_parameters(self, **kwargs) -> bool:
        """Validate that required parameters are present."""
        required_props = self.parameters.get("required", [])
        for prop in required_props:
            if prop not in kwargs or kwargs[prop] is None:
                return False
        return True
