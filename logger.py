"""Comprehensive logging system for Restaurant AI Agent."""

import logging
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import json

class RestaurantAgentLogger:
    """Custom logger for the Restaurant AI Agent with structured logging."""
    
    def __init__(self, name: str = "RestaurantAgent", level: int = logging.INFO):
        """Initialize the logger with custom formatting."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up console and file handlers with custom formatting."""
        
        # Console handler with colored output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # File handler for detailed logs
        file_handler = logging.FileHandler('restaurant-agent.log')
        file_handler.setLevel(logging.DEBUG)
        
        # Custom formatter for better readability
        console_formatter = logging.Formatter(
            '🍽️  %(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_handler.setFormatter(console_formatter)
        file_handler.setFormatter(file_formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def log_user_input(self, message: str, session_info: Optional[Dict] = None):
        """Log user input with session context."""
        log_data = {
            'event_type': 'USER_INPUT',
            'message': message,
            'message_length': len(message),
            'timestamp': datetime.now().isoformat()
        }
        if session_info:
            log_data.update(session_info)
        
        self.logger.info(f"👤 USER INPUT: {message[:100]}{'...' if len(message) > 100 else ''}")
        self.logger.debug(f"User input details: {json.dumps(log_data, indent=2)}")
    
    def log_tool_call(self, tool_name: str, arguments: Dict[str, Any], call_id: str = None):
        """Log when a tool is being called."""
        log_data = {
            'event_type': 'TOOL_CALL',
            'tool_name': tool_name,
            'arguments': arguments,
            'call_id': call_id,
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(f"🔧 TOOL CALL: {tool_name} with args: {list(arguments.keys())}")
        self.logger.debug(f"Tool call details: {json.dumps(log_data, indent=2)}")
    
    def log_tool_result(self, tool_name: str, result: Dict[str, Any], execution_time: float = None):
        """Log tool execution results."""
        success = result.get('success', False)
        status_emoji = "✅" if success else "❌"
        
        log_data = {
            'event_type': 'TOOL_RESULT',
            'tool_name': tool_name,
            'success': success,
            'result_summary': {
                'success': success,
                'message': result.get('message', ''),
                'data_keys': list(result.keys())
            },
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat()
        }
        
        time_str = f" ({execution_time:.2f}s)" if execution_time else ""
        self.logger.info(f"{status_emoji} TOOL RESULT: {tool_name} - {result.get('message', 'No message')}{time_str}")
        self.logger.debug(f"Tool result details: {json.dumps(log_data, indent=2)}")
    
    def log_ai_response(self, response: str, model_info: Optional[Dict] = None):
        """Log AI assistant responses."""
        log_data = {
            'event_type': 'AI_RESPONSE',
            'response': response,
            'response_length': len(response),
            'model_info': model_info,
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(f"🤖 AI RESPONSE: {response[:100]}{'...' if len(response) > 100 else ''}")
        self.logger.debug(f"AI response details: {json.dumps(log_data, indent=2)}")
    
    def log_groq_api_call(self, model: str, message_count: int, has_tools: bool = False):
        """Log Groq API calls."""
        log_data = {
            'event_type': 'GROQ_API_CALL',
            'model': model,
            'message_count': message_count,
            'has_tools': has_tools,
            'timestamp': datetime.now().isoformat()
        }
        
        tool_info = " (with tools)" if has_tools else ""
        self.logger.info(f"🚀 GROQ API: {model} - {message_count} messages{tool_info}")
        self.logger.debug(f"Groq API details: {json.dumps(log_data, indent=2)}")
    
    def log_data_operation(self, operation: str, entity_type: str, entity_id: str = None, details: Dict = None):
        """Log data operations (load, save, search, etc.)."""
        log_data = {
            'event_type': 'DATA_OPERATION',
            'operation': operation,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        
        entity_str = f" ({entity_id})" if entity_id else ""
        self.logger.info(f"💾 DATA: {operation} {entity_type}{entity_str}")
        self.logger.debug(f"Data operation details: {json.dumps(log_data, indent=2)}")
    
    def log_error(self, error: Exception, context: str = "", additional_info: Dict = None):
        """Log errors with context."""
        log_data = {
            'event_type': 'ERROR',
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'additional_info': additional_info or {},
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.error(f"❌ ERROR in {context}: {type(error).__name__} - {str(error)}")
        self.logger.debug(f"Error details: {json.dumps(log_data, indent=2)}")
    
    def log_session_start(self, session_info: Dict = None):
        """Log session start."""
        log_data = {
            'event_type': 'SESSION_START',
            'session_info': session_info or {},
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info("🎯 SESSION STARTED - Restaurant AI Agent initialized")
        self.logger.debug(f"Session details: {json.dumps(log_data, indent=2)}")
    
    def log_conversation_reset(self):
        """Log conversation reset."""
        self.logger.info("🔄 CONVERSATION RESET - Chat history cleared")
        self.logger.debug(f"Conversation reset at {datetime.now().isoformat()}")
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str = ""):
        """Log performance metrics."""
        log_data = {
            'event_type': 'PERFORMANCE_METRIC',
            'metric_name': metric_name,
            'value': value,
            'unit': unit,
            'timestamp': datetime.now().isoformat()
        }
        
        unit_str = f" {unit}" if unit else ""
        self.logger.info(f"📊 METRIC: {metric_name} = {value}{unit_str}")
        self.logger.debug(f"Performance metric: {json.dumps(log_data, indent=2)}")

# Global logger instances
main_logger = RestaurantAgentLogger("RestaurantAgent")
conversation_logger = RestaurantAgentLogger("Conversation")
tool_logger = RestaurantAgentLogger("Tools")
data_logger = RestaurantAgentLogger("Data")
groq_logger = RestaurantAgentLogger("Groq")

def get_logger(name: str = "RestaurantAgent") -> RestaurantAgentLogger:
    """Get a logger instance by name."""
    return RestaurantAgentLogger(name)
