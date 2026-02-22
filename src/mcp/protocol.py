"""MCP Protocol implementation for standardized tool calling and resource management."""

import json
import uuid
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

class MCPMessageType(Enum):
    """MCP message types for protocol communication."""
    INITIALIZE = "initialize"
    INITIALIZED = "initialized"
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    NOTIFICATION = "notification"
    ERROR = "error"

@dataclass
class MCPMessage:
    """Base MCP message structure."""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.id is None and self.method is not None:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        result = {"jsonrpc": self.jsonrpc}
        if self.id is not None:
            result["id"] = self.id
        if self.method is not None:
            result["method"] = self.method
        if self.params is not None:
            result["params"] = self.params
        if self.result is not None:
            result["result"] = self.result
        if self.error is not None:
            result["error"] = self.error
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPMessage':
        """Create message from dictionary."""
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            method=data.get("method"),
            params=data.get("params"),
            result=data.get("result"),
            error=data.get("error")
        )

@dataclass
class MCPTool:
    """MCP Tool definition."""
    name: str
    description: str
    inputSchema: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary."""
        return asdict(self)

@dataclass
class MCPResource:
    """MCP Resource definition."""
    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert resource to dictionary."""
        result = {"uri": self.uri, "name": self.name}
        if self.description:
            result["description"] = self.description
        if self.mimeType:
            result["mimeType"] = self.mimeType
        return result

@dataclass
class MCPToolCall:
    """MCP Tool call request."""
    name: str
    arguments: Dict[str, Any]

@dataclass
class MCPToolResult:
    """MCP Tool call result."""
    content: List[Dict[str, Any]]
    isError: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return asdict(self)

class MCPError(Exception):
    """MCP protocol error."""
    
    def __init__(self, code: int, message: str, data: Optional[Any] = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"MCP Error {code}: {message}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary."""
        result = {"code": self.code, "message": self.message}
        if self.data is not None:
            result["data"] = self.data
        return result

class MCPServer(ABC):
    """Abstract MCP Server implementation."""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.capabilities = {
            "tools": {},
            "resources": {}
        }
    
    @abstractmethod
    def list_tools(self) -> List[MCPTool]:
        """List available tools."""
        pass
    
    @abstractmethod
    def call_tool(self, tool_call: MCPToolCall) -> MCPToolResult:
        """Execute a tool call."""
        pass
    
    @abstractmethod
    def list_resources(self) -> List[MCPResource]:
        """List available resources."""
        pass
    
    @abstractmethod
    def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource by URI."""
        pass
    
    def handle_message(self, message: MCPMessage) -> MCPMessage:
        """Handle incoming MCP message."""
        try:
            if message.method == MCPMessageType.INITIALIZE.value:
                return self._handle_initialize(message)
            elif message.method == MCPMessageType.TOOLS_LIST.value:
                return self._handle_tools_list(message)
            elif message.method == MCPMessageType.TOOLS_CALL.value:
                return self._handle_tools_call(message)
            elif message.method == MCPMessageType.RESOURCES_LIST.value:
                return self._handle_resources_list(message)
            elif message.method == MCPMessageType.RESOURCES_READ.value:
                return self._handle_resources_read(message)
            else:
                raise MCPError(-32601, f"Method not found: {message.method}")
        
        except MCPError as e:
            return MCPMessage(
                jsonrpc="2.0",
                id=message.id,
                error=e.to_dict()
            )
        except Exception as e:
            return MCPMessage(
                jsonrpc="2.0",
                id=message.id,
                error=MCPError(-32603, f"Internal error: {str(e)}").to_dict()
            )
    
    def _handle_initialize(self, message: MCPMessage) -> MCPMessage:
        """Handle initialize request."""
        client_info = message.params or {}
        
        server_info = {
            "protocolVersion": "2024-11-05",
            "capabilities": self.capabilities,
            "serverInfo": {
                "name": self.name,
                "version": self.version
            }
        }
        
        return MCPMessage(
            jsonrpc="2.0",
            id=message.id,
            result=server_info
        )
    
    def _handle_tools_list(self, message: MCPMessage) -> MCPMessage:
        """Handle tools list request."""
        tools = self.list_tools()
        return MCPMessage(
            jsonrpc="2.0",
            id=message.id,
            result={"tools": [tool.to_dict() for tool in tools]}
        )
    
    def _handle_tools_call(self, message: MCPMessage) -> MCPMessage:
        """Handle tool call request."""
        params = message.params or {}
        tool_call = MCPToolCall(
            name=params["name"],
            arguments=params.get("arguments", {})
        )
        
        result = self.call_tool(tool_call)
        return MCPMessage(
            jsonrpc="2.0",
            id=message.id,
            result=result.to_dict()
        )
    
    def _handle_resources_list(self, message: MCPMessage) -> MCPMessage:
        """Handle resources list request."""
        resources = self.list_resources()
        return MCPMessage(
            jsonrpc="2.0",
            id=message.id,
            result={"resources": [resource.to_dict() for resource in resources]}
        )
    
    def _handle_resources_read(self, message: MCPMessage) -> MCPMessage:
        """Handle resource read request."""
        params = message.params or {}
        uri = params.get("uri")
        
        if not uri:
            raise MCPError(-32602, "Missing required parameter: uri")
        
        resource_data = self.read_resource(uri)
        return MCPMessage(
            jsonrpc="2.0",
            id=message.id,
            result=resource_data
        )

class MCPClient:
    """MCP Client for communicating with MCP servers."""
    
    def __init__(self, server_name: str = "restaurant-server"):
        self.server_name = server_name
        self.initialized = False
        self.capabilities = {}
        self._message_id_counter = 0
    
    def _generate_id(self) -> str:
        """Generate unique message ID."""
        self._message_id_counter += 1
        return f"msg_{self._message_id_counter}"
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize connection with MCP server."""
        message = MCPMessage(
            method=MCPMessageType.INITIALIZE.value,
            id=self._generate_id(),
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {}
                },
                "clientInfo": {
                    "name": "restaurant-ai-client",
                    "version": "1.0.0"
                }
            }
        )
        
        # In a real implementation, this would send via WebSocket/HTTP
        # For now, we'll simulate the response
        self.initialized = True
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": True}
            }
        }
    
    async def list_tools(self) -> List[MCPTool]:
        """List available tools from server."""
        if not self.initialized:
            await self.initialize()
        
        message = MCPMessage(
            method=MCPMessageType.TOOLS_LIST.value,
            id=self._generate_id()
        )
        
        # This would be handled by the server connection
        # For now, return empty list - will be implemented in integration
        return []
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> MCPToolResult:
        """Call a tool on the server."""
        if not self.initialized:
            await self.initialize()
        
        message = MCPMessage(
            method=MCPMessageType.TOOLS_CALL.value,
            id=self._generate_id(),
            params={
                "name": name,
                "arguments": arguments
            }
        )
        
        # This would be handled by the server connection
        # For now, return empty result - will be implemented in integration
        return MCPToolResult(content=[])
    
    async def list_resources(self) -> List[MCPResource]:
        """List available resources from server."""
        if not self.initialized:
            await self.initialize()
        
        message = MCPMessage(
            method=MCPMessageType.RESOURCES_LIST.value,
            id=self._generate_id()
        )
        
        # This would be handled by the server connection
        return []
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource from the server."""
        if not self.initialized:
            await self.initialize()
        
        message = MCPMessage(
            method=MCPMessageType.RESOURCES_READ.value,
            id=self._generate_id(),
            params={"uri": uri}
        )
        
        # This would be handled by the server connection
        return {"contents": []}
