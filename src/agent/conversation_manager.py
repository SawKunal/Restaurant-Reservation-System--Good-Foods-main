"""Main conversation manager for the restaurant AI agent with MCP protocol."""

import json
import time
from typing import Dict, List, Any, Optional
from src.agent.groq_client import GroqClient
from src.mcp.restaurant_client import get_mcp_client
from src.utils.logger import conversation_logger, tool_logger

class ConversationManager:
    """Manages the conversation flow and tool execution for the restaurant AI agent."""
    
    def __init__(self):
        """Initialize the conversation manager with MCP client."""
        self.groq_client = GroqClient()
        self.conversation_history: List[Dict[str, str]] = []
        
        # Initialize MCP client for tool calling
        self.mcp_client = get_mcp_client()
        
        # System prompt for the AI agent with MCP protocol
        # Design: Structural prevention of hallucinations through clear identity and process
        self.system_prompt = """You are a GoodFoods restaurant reservation assistant. Your responses are grounded exclusively in verified data from your tool systems. You facilitate restaurant searches, availability checks, and reservation management.

## Your Role

You help users find restaurants, verify table availability, and manage bookings. Every restaurant detail, availability status, and reservation confirmation comes directly from querying your tools. You never provide information that hasn't been retrieved from these systems.

## Available Tools

1. **search_restaurants** - Query restaurants by cuisine, location, or capacity
2. **check_availability** - Verify table availability for specific date/time/party size
3. **make_reservation** - Create confirmed bookings with complete user information
4. **cancel_reservation** - Cancel existing reservations by ID

## Operating Protocol

**When users ask about restaurants:**
- Identify their criteria (cuisine, location, party size, date, time)
- Call `search_restaurants` with the available parameters
- Present results using exact names and details from the tool response
- If results are empty, state this clearly: "I found no restaurants matching those criteria. Would you like to try different search terms?"

**When users want to check availability:**
- Confirm you have: restaurant ID, date (YYYY-MM-DD), time, party size
- Call `check_availability` with these parameters
- Report availability exactly as returned
- If unavailable, explain why based on tool response (no tables, already booked, etc.)

**When users want to make a reservation:**
Follow this process to collect information and complete the booking:

STEP 1 - Gather Required Information:
Check if you have all required fields:
- Restaurant (from search results - use restaurant_id)
- Date (YYYY-MM-DD format)
- Time (HH:MM format)
- Party size (number of people)
- Customer name (full name from user)
- Customer phone (phone number from user)
- Customer email (email address from user)

STEP 2 - Request Missing Information:
If ANY field is missing, ask the user for it. For example:
- "What name should the reservation be under?"
- "What phone number can we reach you at?"
- "What email should we send the confirmation to?"

STEP 3 - Complete the Reservation:
Once you have ALL seven fields with actual values from the conversation, call make_reservation with those values.

CRITICAL RULES:
✓ DO use data when the user has explicitly provided it in their messages
✓ DO extract real names, phone numbers, and emails from user responses
✓ DO call make_reservation once you have all real information

✗ DON'T use placeholder data like "your_email@example.com", "Your Name", "1234567890"
✗ DON'T fabricate or assume user information
✗ DON'T call make_reservation if you're missing any required field

Example Flow:
User: "I want to book a table"
You: "I'll need some information: What name, phone number, and email should I use?"
User: "ujjwal mishra, 8887627311, ujjman@gmail.com"
You: [Extract these values → Call make_reservation with them]

**When users want to cancel:**
- Confirm the reservation ID
- Call `cancel_reservation`
- Confirm cancellation based on tool response

## Handling Incomplete Information

If you lack required information, ask specific questions:
- "What cuisine type interests you?"
- "What date and time would you prefer? (Please use MM-DD format for date)"
- "How many people will be dining?"
- "Which location or neighborhood are you interested in?"

Never assume or infer missing details. Always verify through direct questions or tool calls.

## Response Behavior

**Information Sources:**
- All restaurant names, addresses, cuisine types, and capacities come from `search_restaurants` results
- All availability information comes from `check_availability` results
- All confirmation details come from `make_reservation` results

**When Uncertain:**
- If search parameters are unclear: ask for clarification
- If no results match: report this honestly without suggesting alternatives you haven't verified
- If tools fail: explain the technical issue without fabricating workarounds

**Outside Scope:**
For non-reservation queries: "I specialize in restaurant reservations. I can search restaurants, check availability, make bookings, or cancel reservations. How can I assist with your dining plans?"

## Communication Style

- Be concise and direct
- Use exact terminology from tool results
- Ask questions when you need information
- Acknowledge limitations transparently
- Guide users toward achievable outcomes within your capabilities

## Core Commitment

Your accuracy is absolute. Every fact you state must originate from a tool call. When in doubt, query your tools or ask for clarification. Never fill gaps with assumptions, estimates, or general knowledge.
"""

        
        # Initialize conversation with system prompt
        self.conversation_history.append({
            "role": "system",
            "content": self.system_prompt
        })
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get all tool definitions for function calling via MCP."""
        conversation_logger.logger.info("🔧 CONV MGR: Getting tool definitions via MCP client")
        
        try:
            # Get tools from MCP client in Groq-compatible format
            tool_definitions = self.mcp_client.get_tools_for_groq()
            
            conversation_logger.logger.info(f"🔧 CONV MGR: Retrieved {len(tool_definitions)} tools via MCP")
            return tool_definitions
            
        except Exception as e:
            conversation_logger.log_error(e, "get_tool_definitions_mcp")
            # Fallback to empty list if MCP fails
            return []
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific tool via MCP protocol."""
        conversation_logger.logger.info(f"🔧 CONV MGR: Executing tool '{tool_name}' via MCP with args: {arguments}")
        
        try:
            # Log tool call start
            tool_logger.log_tool_call(tool_name, arguments)
            
            # Execute tool via MCP client with timing
            start_time = time.time()
            result = self.mcp_client.execute_tool_sync(tool_name, arguments)
            execution_time = time.time() - start_time
            
            # Log tool result
            tool_logger.log_tool_result(tool_name, result, execution_time)
            
            conversation_logger.logger.info(f"✅ CONV MGR: Tool '{tool_name}' executed successfully via MCP")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time if 'start_time' in locals() else None
            error_result = {
                "success": False,
                "message": f"Error executing {tool_name} via MCP: {str(e)}"
            }
            
            tool_logger.log_error(e, f"execute_tool_mcp({tool_name})", {
                'arguments': arguments,
                'execution_time': execution_time
            })
            tool_logger.log_tool_result(tool_name, error_result, execution_time)
            
            return error_result
    
    def process_message(self, user_message: str) -> str:
        """
        Process a user message and return the AI response.
        
        Args:
            user_message: The user's input message
            
        Returns:
            The AI agent's response
        """
        try:
            # Log user input
            conversation_logger.log_user_input(user_message, {
                'conversation_length': len(self.conversation_history),
                'has_previous_context': len(self.conversation_history) > 1
            })
            
            # Add user message to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Get response from Groq with tool calling
            tool_definitions = self.get_tool_definitions()
            
            # Log Groq API call
            conversation_logger.log_groq_api_call(
                model=self.groq_client.model,
                message_count=len(self.conversation_history),
                has_tools=len(tool_definitions) > 0
            )
            
            response = self.groq_client.chat_completion(
                messages=self.conversation_history,
                tools=tool_definitions,
                stream=False
            )
            
            if not response:
                error_msg = "I apologize, but I'm experiencing technical difficulties. Please try again."
                conversation_logger.log_error(Exception("No response from Groq API"), "process_message")
                return error_msg
            
            # Check if the model wants to call a tool
            if response.get("tool_calls"):
                return self._handle_tool_calls(response)
            else:
                # Regular text response
                assistant_message = response.get("content", "")
                
                # Log AI response
                conversation_logger.log_ai_response(assistant_message, {
                    'model': self.groq_client.model,
                    'response_type': 'direct_text'
                })
                
                # Add assistant response to conversation history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": assistant_message
                })
                
                return assistant_message
            
        except Exception as e:
            error_message = f"I encountered an error: {str(e)}. Please try again."
            
            # Log error
            conversation_logger.log_error(e, "process_message", {
                'user_message': user_message[:100]
            })
            
            # Add error to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": error_message
            })
            
            return error_message
    
    def _handle_tool_calls(self, response: Dict[str, Any]) -> str:
        """Handle tool calling from the AI response."""
        try:
            tool_calls = response.get("tool_calls", [])
            tool_results = []
            
            # Add assistant message with tool calls to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response.get("content", ""),
                "tool_calls": response.get("tool_calls")
            })
            
            # Execute each tool call
            for tool_call in tool_calls:
                function_name = tool_call["function"]["name"]
                try:
                    arguments = json.loads(tool_call["function"]["arguments"])
                except json.JSONDecodeError:
                    arguments = {}
                
                # Execute the tool
                result = self.execute_tool(function_name, arguments)
                tool_results.append({
                    "tool_call_id": tool_call["id"],
                    "result": result
                })
                
                # Add tool result to conversation history
                self.conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(result)
                })
            
            # Get final response from the model after tool execution
            final_response = self.groq_client.chat_completion(
                messages=self.conversation_history,
                tools=self.get_tool_definitions(),
                stream=False
            )
            
            if final_response:
                final_content = final_response.get("content", "")
                
                # Add final response to conversation history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_content
                })
                
                return final_content
            else:
                return "I completed the requested action but encountered an issue generating a response."
                
        except Exception as e:
            error_msg = f"Error handling tool calls: {str(e)}"
            self.conversation_history.append({
                "role": "assistant",
                "content": error_msg
            })
            return error_msg
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the current conversation history."""
        # Return only user and assistant messages (exclude system and tool messages)
        return [
            msg for msg in self.conversation_history 
            if msg["role"] in ["user", "assistant"] and "tool_calls" not in msg
        ]
    
    def clear_conversation(self):
        """Clear the conversation history and start fresh."""
        self.conversation_history = [
            {
                "role": "system", 
                "content": self.system_prompt
            }
        ]
    
    def stream_response(self, user_message: str):
        """
        Stream the AI response for real-time display.
        
        Args:
            user_message: The user's input message
            
        Yields:
            Chunks of the AI response as they're generated
        """
        try:
            # Add user message to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Get streaming response from Groq
            tool_definitions = self.get_tool_definitions()
            
            # First, check if we need to call tools (non-streaming)
            response = self.groq_client.chat_completion(
                messages=self.conversation_history,
                tools=tool_definitions,
                stream=False
            )
            
            if response and response.get("tool_calls"):
                # Handle tool calls first, then stream final response
                final_response = self._handle_tool_calls(response)
                yield final_response
            else:
                # Stream regular response
                stream = self.groq_client.chat_completion(
                    messages=self.conversation_history,
                    tools=tool_definitions,
                    stream=True
                )
                
                full_response = ""
                for chunk in stream:
                    if chunk:
                        full_response += chunk
                        yield chunk
                
                # Add complete response to conversation history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": full_response
                })
                
        except Exception as e:
            error_message = f"Error during streaming: {str(e)}"
            yield error_message
