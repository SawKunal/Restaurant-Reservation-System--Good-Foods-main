"""Restaurant MCP Server implementation for tool calling and resource management."""

import json
import asyncio
from typing import Dict, List, Any, Optional
from src.mcp.protocol import MCPServer, MCPTool, MCPResource, MCPToolCall, MCPToolResult, MCPError
from src.tools.search_restaurants import SearchRestaurantsTool
from src.tools.check_availability import CheckAvailabilityTool
from src.tools.make_reservation import MakeReservationTool
from src.tools.cancel_reservation import CancelReservationTool
from src.data.restaurant_loader import get_restaurant_loader
from src.utils.logger import tool_logger

# Import reservation manager - create if doesn't exist
try:
    from src.data.reservations import get_reservation_manager
except ImportError:
    # Create basic reservation manager if it doesn't exist
    class BasicReservationManager:
        def get_all_reservations(self):
            return []
        def get_active_reservations(self):
            return []
    
    def get_reservation_manager():
        return BasicReservationManager()

class RestaurantMCPServer(MCPServer):
    """MCP Server implementation for restaurant reservation system."""
    
    def __init__(self):
        """Initialize restaurant MCP server."""
        super().__init__("restaurant-server", "1.0.0")
        
        # Initialize restaurant tools
        self.restaurant_tools = {
            "search_restaurants": SearchRestaurantsTool(),
            "check_availability": CheckAvailabilityTool(),
            "make_reservation": MakeReservationTool(),
            "cancel_reservation": CancelReservationTool()
        }
        
        # Initialize data managers
        self.restaurant_loader = get_restaurant_loader()
        self.reservation_manager = get_reservation_manager()
        
        # Set MCP server capabilities
        self.capabilities = {
            "tools": {
                "listChanged": True
            },
            "resources": {
                "subscribe": True,
                "listChanged": True
            }
        }
        
        tool_logger.logger.info("🔧 MCP SERVER: Restaurant MCP Server initialized")
    
    def list_tools(self) -> List[MCPTool]:
        """List available restaurant tools via MCP protocol."""
        tool_logger.logger.info("📋 MCP SERVER: Listing available tools")
        
        mcp_tools = []
        
        for tool_name, tool_instance in self.restaurant_tools.items():
            mcp_tool = MCPTool(
                name=tool_name,
                description=tool_instance.description,
                inputSchema=tool_instance.parameters
            )
            mcp_tools.append(mcp_tool)
        
        tool_logger.logger.info(f"📋 MCP SERVER: Listed {len(mcp_tools)} tools: {list(self.restaurant_tools.keys())}")
        return mcp_tools
    
    def call_tool(self, tool_call: MCPToolCall) -> MCPToolResult:
        """Execute a restaurant tool via MCP protocol."""
        tool_name = tool_call.name
        arguments = tool_call.arguments
        
        tool_logger.logger.info(f"🔧 MCP SERVER: Executing tool '{tool_name}' with args: {arguments}")
        
        try:
            # Check if tool exists
            if tool_name not in self.restaurant_tools:
                raise MCPError(-32601, f"Tool not found: {tool_name}")
            
            # Get the tool instance
            tool_instance = self.restaurant_tools[tool_name]
            
            # Execute the tool
            result = tool_instance.execute(**arguments)
            
            # Convert result to MCP format
            mcp_result = MCPToolResult(
                content=[
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ],
                isError=not result.get("success", True)
            )
            
            tool_logger.logger.info(f"✅ MCP SERVER: Tool '{tool_name}' executed successfully")
            return mcp_result
        
        except Exception as e:
            tool_logger.log_error(e, f"mcp_tool_call({tool_name})", {"arguments": arguments})
            
            error_result = MCPToolResult(
                content=[
                    {
                        "type": "text", 
                        "text": json.dumps({
                            "success": False,
                            "error": str(e),
                            "message": f"Error executing tool {tool_name}: {str(e)}"
                        })
                    }
                ],
                isError=True
            )
            
            return error_result
    
    def list_resources(self) -> List[MCPResource]:
        """List available restaurant resources via MCP protocol."""
        tool_logger.logger.info("📚 MCP SERVER: Listing available resources")
        
        resources = [
            MCPResource(
                uri="restaurant://restaurants/all",
                name="All Restaurants",
                description="Complete list of all available restaurants",
                mimeType="application/json"
            ),
            MCPResource(
                uri="restaurant://restaurants/cuisines",
                name="Restaurant Cuisines",
                description="List of all available cuisine types",
                mimeType="application/json"
            ),
            MCPResource(
                uri="restaurant://restaurants/locations",
                name="Restaurant Locations", 
                description="List of all restaurant locations",
                mimeType="application/json"
            ),
            MCPResource(
                uri="restaurant://reservations/all",
                name="All Reservations",
                description="Complete list of all reservations",
                mimeType="application/json"
            ),
            MCPResource(
                uri="restaurant://reservations/active",
                name="Active Reservations",
                description="List of active reservations only",
                mimeType="application/json"
            )
        ]
        
        tool_logger.logger.info(f"📚 MCP SERVER: Listed {len(resources)} resources")
        return resources
    
    def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a restaurant resource by URI via MCP protocol."""
        tool_logger.logger.info(f"📖 MCP SERVER: Reading resource: {uri}")
        
        try:
            if uri == "restaurant://restaurants/all":
                restaurants = self.restaurant_loader.get_all_restaurants()
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps([r.to_dict() for r in restaurants], indent=2)
                        }
                    ]
                }
            
            elif uri == "restaurant://restaurants/cuisines":
                restaurants = self.restaurant_loader.get_all_restaurants()
                cuisines = list(set(r.cuisine_type for r in restaurants))
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(sorted(cuisines), indent=2)
                        }
                    ]
                }
            
            elif uri == "restaurant://restaurants/locations":
                restaurants = self.restaurant_loader.get_all_restaurants()
                locations = list(set(r.location for r in restaurants))
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json", 
                            "text": json.dumps(sorted(locations), indent=2)
                        }
                    ]
                }
            
            elif uri == "restaurant://reservations/all":
                reservations = self.reservation_manager.get_all_reservations()
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps([r.to_dict() for r in reservations], indent=2)
                        }
                    ]
                }
            
            elif uri == "restaurant://reservations/active":
                reservations = self.reservation_manager.get_active_reservations()
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps([r.to_dict() for r in reservations], indent=2)
                        }
                    ]
                }
            
            else:
                raise MCPError(-32602, f"Unknown resource URI: {uri}")
        
        except Exception as e:
            tool_logger.log_error(e, f"mcp_read_resource({uri})")
            raise MCPError(-32603, f"Error reading resource {uri}: {str(e)}")

class RestaurantMCPServerManager:
    """Manager for running the Restaurant MCP Server."""
    
    def __init__(self):
        """Initialize server manager."""
        self.server = RestaurantMCPServer()
        self.running = False
        
    def start_server(self, host: str = "localhost", port: int = 8000):
        """Start the MCP server."""
        tool_logger.logger.info(f"🚀 MCP SERVER: Starting server on {host}:{port}")
        self.running = True
        
        # In a real implementation, this would start an HTTP/WebSocket server
        # For our integration, we'll use direct method calls
        tool_logger.logger.info("✅ MCP SERVER: Server started successfully")
        
    def stop_server(self):
        """Stop the MCP server."""
        tool_logger.logger.info("🛑 MCP SERVER: Stopping server")
        self.running = False
        tool_logger.logger.info("✅ MCP SERVER: Server stopped")
    
    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a direct MCP request (for testing/integration)."""
        from src.mcp.protocol import MCPMessage
        
        try:
            # Parse request as MCP message
            message = MCPMessage.from_dict(request_data)
            
            # Handle the message
            response = self.server.handle_message(message)
            
            return response.to_dict()
        
        except Exception as e:
            tool_logger.log_error(e, "mcp_handle_request", {"request": request_data})
            return {
                "jsonrpc": "2.0",
                "id": request_data.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }

# Global server instance
_mcp_server_manager = None

def get_mcp_server_manager() -> RestaurantMCPServerManager:
    """Get global MCP server manager instance."""
    global _mcp_server_manager
    if _mcp_server_manager is None:
        _mcp_server_manager = RestaurantMCPServerManager()
    return _mcp_server_manager
