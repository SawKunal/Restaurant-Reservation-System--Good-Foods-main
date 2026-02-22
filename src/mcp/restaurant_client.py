"""Restaurant MCP Client implementation for communicating with MCP server."""

import json
import asyncio
from typing import Dict, List, Any, Optional
from src.mcp.protocol import MCPClient, MCPTool, MCPResource, MCPMessage, MCPToolResult
from src.mcp.restaurant_server import get_mcp_server_manager
from src.utils.logger import conversation_logger, tool_logger

class RestaurantMCPClient(MCPClient):
    """MCP Client implementation for restaurant reservation system."""
    
    def __init__(self):
        """Initialize restaurant MCP client."""
        super().__init__("restaurant-server")
        self.server_manager = get_mcp_server_manager()
        self._tools_cache: Optional[List[MCPTool]] = None
        self._resources_cache: Optional[List[MCPResource]] = None
        
        # Start the server
        self.server_manager.start_server()
        
        conversation_logger.logger.info("🔗 MCP CLIENT: Restaurant MCP Client initialized")
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize connection with MCP server."""
        conversation_logger.logger.info("🚀 MCP CLIENT: Initializing connection with server")
        
        request = {
            "jsonrpc": "2.0",
            "id": self._generate_id(),
            "method": "initialize",
            "params": {
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
        }
        
        # Handle request through server manager
        response = self.server_manager.handle_request(request)
        
        if "error" in response:
            raise Exception(f"MCP initialization failed: {response['error']}")
        
        self.initialized = True
        self.capabilities = response.get("result", {}).get("capabilities", {})
        
        conversation_logger.logger.info("✅ MCP CLIENT: Successfully initialized connection")
        return response.get("result", {})
    
    async def list_tools(self) -> List[MCPTool]:
        """List available tools from server."""
        if not self.initialized:
            await self.initialize()
        
        # Return cached tools if available
        if self._tools_cache is not None:
            return self._tools_cache
        
        conversation_logger.logger.info("📋 MCP CLIENT: Requesting tools list from server")
        
        request = {
            "jsonrpc": "2.0",
            "id": self._generate_id(),
            "method": "tools/list"
        }
        
        # Handle request through server manager
        response = self.server_manager.handle_request(request)
        
        if "error" in response:
            raise Exception(f"Failed to list tools: {response['error']}")
        
        # Parse tools from response
        tools_data = response.get("result", {}).get("tools", [])
        tools = []
        
        for tool_data in tools_data:
            tool = MCPTool(
                name=tool_data["name"],
                description=tool_data["description"],
                inputSchema=tool_data["inputSchema"]
            )
            tools.append(tool)
        
        # Cache tools
        self._tools_cache = tools
        
        conversation_logger.logger.info(f"📋 MCP CLIENT: Retrieved {len(tools)} tools from server")
        return tools
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> MCPToolResult:
        """Call a tool on the server."""
        if not self.initialized:
            await self.initialize()
        
        tool_logger.logger.info(f"🔧 MCP CLIENT: Calling tool '{name}' with args: {arguments}")
        
        request = {
            "jsonrpc": "2.0",
            "id": self._generate_id(),
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments
            }
        }
        
        # Handle request through server manager
        response = self.server_manager.handle_request(request)
        
        if "error" in response:
            error_msg = response["error"].get("message", "Unknown error")
            tool_logger.log_error(Exception(error_msg), f"mcp_client_call_tool({name})", {"arguments": arguments})
            
            return MCPToolResult(
                content=[
                    {
                        "type": "text",
                        "text": json.dumps({
                            "success": False,
                            "error": error_msg,
                            "message": f"MCP tool call failed: {error_msg}"
                        })
                    }
                ],
                isError=True
            )
        
        # Parse result from response
        result_data = response.get("result", {})
        
        tool_result = MCPToolResult(
            content=result_data.get("content", []),
            isError=result_data.get("isError", False)
        )
        
        tool_logger.logger.info(f"✅ MCP CLIENT: Tool '{name}' executed successfully")
        return tool_result
    
    async def list_resources(self) -> List[MCPResource]:
        """List available resources from server."""
        if not self.initialized:
            await self.initialize()
        
        # Return cached resources if available
        if self._resources_cache is not None:
            return self._resources_cache
        
        conversation_logger.logger.info("📚 MCP CLIENT: Requesting resources list from server")
        
        request = {
            "jsonrpc": "2.0",
            "id": self._generate_id(),
            "method": "resources/list"
        }
        
        # Handle request through server manager
        response = self.server_manager.handle_request(request)
        
        if "error" in response:
            raise Exception(f"Failed to list resources: {response['error']}")
        
        # Parse resources from response
        resources_data = response.get("result", {}).get("resources", [])
        resources = []
        
        for resource_data in resources_data:
            resource = MCPResource(
                uri=resource_data["uri"],
                name=resource_data["name"],
                description=resource_data.get("description"),
                mimeType=resource_data.get("mimeType")
            )
            resources.append(resource)
        
        # Cache resources
        self._resources_cache = resources
        
        conversation_logger.logger.info(f"📚 MCP CLIENT: Retrieved {len(resources)} resources from server")
        return resources
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource from the server."""
        if not self.initialized:
            await self.initialize()
        
        conversation_logger.logger.info(f"📖 MCP CLIENT: Reading resource: {uri}")
        
        request = {
            "jsonrpc": "2.0",
            "id": self._generate_id(),
            "method": "resources/read",
            "params": {"uri": uri}
        }
        
        # Handle request through server manager
        response = self.server_manager.handle_request(request)
        
        if "error" in response:
            raise Exception(f"Failed to read resource {uri}: {response['error']}")
        
        result = response.get("result", {})
        conversation_logger.logger.info(f"✅ MCP CLIENT: Successfully read resource: {uri}")
        
        return result
    
    def get_available_tool_names(self) -> List[str]:
        """Get list of available tool names (synchronous helper)."""
        if self._tools_cache is None:
            # Initialize tools synchronously
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                tools = loop.run_until_complete(self.list_tools())
                return [tool.name for tool in tools]
            finally:
                loop.close()
        
        return [tool.name for tool in self._tools_cache]
    
    def execute_tool_sync(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool synchronously (helper for conversation manager)."""
        import asyncio
        
        # Create new event loop for synchronous execution
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Execute tool call
            result = loop.run_until_complete(self.call_tool(name, arguments))
            
            # Parse result content
            if result.content and len(result.content) > 0:
                content_text = result.content[0].get("text", "{}")
                try:
                    parsed_result = json.loads(content_text)
                    return parsed_result
                except json.JSONDecodeError:
                    return {
                        "success": False,
                        "error": "Failed to parse tool result",
                        "raw_content": content_text
                    }
            else:
                return {
                    "success": False,
                    "error": "Empty tool result",
                    "isError": result.isError
                }
        
        except Exception as e:
            tool_logger.log_error(e, f"mcp_client_execute_sync({name})", {"arguments": arguments})
            return {
                "success": False,
                "error": str(e),
                "message": f"Error executing tool {name}: {str(e)}"
            }
        
        finally:
            loop.close()
    
    def get_tools_for_groq(self) -> List[Dict[str, Any]]:
        """Get tools in Groq-compatible format for function calling."""
        if self._tools_cache is None:
            # Initialize tools
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.list_tools())
            finally:
                loop.close()
        
        # Convert MCP tools to Groq format
        groq_tools = []
        for tool in self._tools_cache or []:
            groq_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            }
            groq_tools.append(groq_tool)
        
        return groq_tools

# Global client instance
_mcp_client = None

def get_mcp_client() -> RestaurantMCPClient:
    """Get global MCP client instance."""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = RestaurantMCPClient()
    return _mcp_client
