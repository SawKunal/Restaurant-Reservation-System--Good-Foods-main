"""Groq API client for handling LLM interactions."""

import json
import time
from typing import Dict, List, Any, Optional, Generator
from groq import Groq
from src.config.settings import get_settings
from src.utils.logger import groq_logger

class GroqClient:
    """Client for interacting with Groq API."""
    
    def __init__(self):
        """Initialize Groq client with API key from settings."""
        self.settings = get_settings()
        self.settings.validate()
        self.client = Groq(api_key=self.settings.GROQ_API_KEY)
        self.model = self.settings.DEFAULT_MODEL
    
    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       tools: Optional[List[Dict[str, Any]]] = None,
                       stream: bool = False) -> Any:
        """
        Create a chat completion with optional tool calling.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            tools: Optional list of tool definitions for function calling
            stream: Whether to stream the response
            
        Returns:
            Chat completion response or generator for streaming
        """
        start_time = time.time()
        
        # Log API call details
        groq_logger.log_groq_api_call(
            model=self.model,
            message_count=len(messages),
            has_tools=tools is not None and len(tools) > 0
        )
        
        try:
            completion_kwargs = {
                "messages": messages,
                "model": self.model,
                "temperature": self.settings.TEMPERATURE,
                "max_tokens": self.settings.MAX_TOKENS,
                "stream": stream
            }
            
            # Add tools if provided
            if tools:
                completion_kwargs["tools"] = tools
                completion_kwargs["tool_choice"] = "auto"
                groq_logger.log_performance_metric("tools_provided", len(tools), "count")
            
            # Log request details
            total_chars = sum(len(str(msg.get('content', ''))) for msg in messages)
            groq_logger.log_performance_metric("request_characters", total_chars, "chars")
            
            response = self.client.chat.completions.create(**completion_kwargs)
            
            # Log API call timing
            api_time = time.time() - start_time
            groq_logger.log_performance_metric("groq_api_response_time", api_time, "seconds")
            
            if stream:
                groq_logger.logger.info("🌊 GROQ STREAM: Starting streaming response")
                return self._handle_streaming_response(response, start_time)
            else:
                return self._handle_standard_response(response, start_time)
                
        except Exception as e:
            api_time = time.time() - start_time
            groq_logger.log_error(e, "chat_completion", {
                'model': self.model,
                'message_count': len(messages),
                'has_tools': tools is not None,
                'stream': stream,
                'api_time': api_time
            })
            groq_logger.log_performance_metric("groq_api_error_time", api_time, "seconds")
            return None
    
    def _handle_standard_response(self, response: Any, start_time: float) -> Dict[str, Any]:
        """Handle non-streaming response."""
        choice = response.choices[0]
        message = choice.message
        
        result = {
            "content": message.content,
            "role": message.role,
            "tool_calls": None
        }
        
        # Handle tool calls if present
        if hasattr(message, 'tool_calls') and message.tool_calls:
            result["tool_calls"] = []
            tool_names = []
            for tool_call in message.tool_calls:
                tool_names.append(tool_call.function.name)
                result["tool_calls"].append({
                    "id": tool_call.id,
                    "type": tool_call.type,
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                })
            
            # Log tool calls requested by AI
            groq_logger.logger.info(f"🔧 GROQ TOOL CALLS: {', '.join(tool_names)}")
        
        # Log response details
        response_chars = len(message.content) if message.content else 0
        total_time = time.time() - start_time
        
        groq_logger.log_performance_metric("response_characters", response_chars, "chars")
        groq_logger.log_performance_metric("total_completion_time", total_time, "seconds")
        
        return result
    
    def _handle_streaming_response(self, response: Any, start_time: float) -> Generator[str, None, None]:
        """Handle streaming response."""
        total_chunks = 0
        total_chars = 0
        
        for chunk in response:
            if chunk.choices[0].delta.content:
                chunk_content = chunk.choices[0].delta.content
                total_chunks += 1
                total_chars += len(chunk_content)
                yield chunk_content
        
        # Log streaming metrics
        total_time = time.time() - start_time
        groq_logger.log_performance_metric("stream_chunks", total_chunks, "count")
        groq_logger.log_performance_metric("stream_characters", total_chars, "chars")
        groq_logger.log_performance_metric("stream_total_time", total_time, "seconds")
        groq_logger.logger.info(f"🌊 GROQ STREAM COMPLETE: {total_chunks} chunks, {total_chars} chars in {total_time:.2f}s")
    
    def create_tool_definition(self, name: str, description: str, 
                              parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a tool definition for function calling.
        
        Args:
            name: Function name
            description: Function description
            parameters: JSON schema for function parameters
            
        Returns:
            Tool definition dictionary
        """
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters
            }
        }
