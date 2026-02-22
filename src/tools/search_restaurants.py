"""Search restaurants tool."""

import json
from typing import Dict, Any, List, Optional
from src.tools.base_tool import BaseTool
from src.data.restaurant_loader import get_restaurant_loader
from src.utils.logger import tool_logger

class SearchRestaurantsTool(BaseTool):
    """Tool for searching restaurants by various criteria."""
    
    @property
    def name(self) -> str:
        return "search_restaurants"
    
    @property
    def description(self) -> str:
        return "Search for restaurants based on cuisine type, location, features (like romantic, family-friendly), price range, and minimum rating. Returns a list of matching restaurants with their details."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "cuisine": {
                    "type": "string",
                    "description": "Cuisine type (e.g., 'Italian', 'Chinese', 'Mexican')",
                },
                "location": {
                    "type": "string",
                    "description": "Location area (e.g., 'Downtown', 'Westside', 'Uptown')",
                },
                "features": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of desired features (e.g., ['romantic', 'outdoor-seating', 'family-friendly'])",
                },
                "price_range": {
                    "type": "string",
                    "enum": ["$20", "$30", "$40", "$50"],
                    "description": "Price range from $20 (cheap) to $50 (expensive)",
                },
                "min_rating": {
                    "type": "number",
                    "description": "Minimum rating (0-5 scale)",
                    "minimum": 0,
                    "maximum": 5
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 10)",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 10
                }
            },
            "required": []
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute restaurant search."""
        # Log search parameters
        search_params = {
            "cuisine": kwargs.get("cuisine"),
            "location": kwargs.get("location"),
            "features": kwargs.get("features"),
            "price_range": kwargs.get("price_range"),
            "min_rating": kwargs.get("min_rating"),
            "limit": kwargs.get("limit", 10)
        }
        
        tool_logger.logger.info(f"🔍 SEARCH RESTAURANTS: {search_params}")
        
        try:
            restaurant_loader = get_restaurant_loader()
            
            # Extract search parameters
            cuisine = kwargs.get("cuisine")
            location = kwargs.get("location")
            features = kwargs.get("features")
            price_range = kwargs.get("price_range")
            min_rating = kwargs.get("min_rating")
            limit = kwargs.get("limit", 10)
            
            # Search restaurants
            restaurants = restaurant_loader.search_restaurants(
                cuisine=cuisine,
                location=location,
                features=features,
                price_range=price_range,
                min_rating=min_rating
            )
            
            # Limit results
            restaurants = restaurants[:limit]
            
            if not restaurants:
                return {
                    "success": True,
                    "message": "No restaurants found matching your criteria.",
                    "restaurants": [],
                    "count": 0
                }
            
            # Format restaurant information for response
            restaurant_list = []
            for restaurant in restaurants:
                restaurant_info = {
                    "id": restaurant.id,
                    "name": restaurant.name,
                    "cuisine_type": restaurant.cuisine_type,
                    "location": restaurant.location,
                    "address": restaurant.address,
                    "phone": restaurant.phone,
                    "capacity": restaurant.capacity,
                    "price_range": restaurant.price_range,
                    "rating": restaurant.rating,
                    "description": restaurant.description,
                    "features": restaurant.features,
                    "opening_hours": restaurant.opening_hours
                }
                restaurant_list.append(restaurant_info)
            
            return {
                "success": True,
                "message": f"Found {len(restaurants)} restaurants matching your criteria.",
                "restaurants": restaurant_list,
                "count": len(restaurants)
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error searching restaurants: {str(e)}",
                "restaurants": [],
                "count": 0
            }
