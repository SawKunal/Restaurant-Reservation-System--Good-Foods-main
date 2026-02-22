"""Restaurant data loader and management."""

import json
import os
from typing import List, Optional, Dict, Any
from src.models.restaurant import Restaurant
from src.config.settings import get_settings
from src.utils.logger import data_logger

class RestaurantLoader:
    """Handles loading and managing restaurant data."""
    
    def __init__(self):
        """Initialize restaurant loader."""
        self.settings = get_settings()
        self.data_file = self.settings.RESTAURANT_DATA_FILE
        self._restaurants: List[Restaurant] = []
        self.load_restaurants()
    
    def load_restaurants(self):
        """Load restaurants from JSON file."""
        try:
            data_logger.log_data_operation("LOAD", "restaurants", details={"file": self.data_file})
            
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._restaurants = [Restaurant.from_dict(restaurant) for restaurant in data]
                
                data_logger.log_data_operation("LOAD_SUCCESS", "restaurants", 
                                             details={"count": len(self._restaurants), "file": self.data_file})
            else:
                data_logger.log_error(FileNotFoundError(f"Restaurant data file not found: {self.data_file}"), 
                                    "load_restaurants")
                self._restaurants = []
        except Exception as e:
            data_logger.log_error(e, "load_restaurants", {"file": self.data_file})
            self._restaurants = []
    
    def save_restaurants(self):
        """Save restaurants to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                data = [restaurant.to_dict() for restaurant in self._restaurants]
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving restaurants: {str(e)}")
    
    def get_all_restaurants(self) -> List[Restaurant]:
        """Get all restaurants."""
        return self._restaurants.copy()
    
    def get_restaurant_by_id(self, restaurant_id: str) -> Optional[Restaurant]:
        """Get restaurant by ID."""
        for restaurant in self._restaurants:
            if restaurant.id == restaurant_id:
                return restaurant
        return None
    
    def search_restaurants(self, 
                          cuisine: Optional[str] = None,
                          location: Optional[str] = None, 
                          features: Optional[List[str]] = None,
                          price_range: Optional[str] = None,
                          min_rating: Optional[float] = None) -> List[Restaurant]:
        """
        Search restaurants by various criteria.
        
        Args:
            cuisine: Cuisine type filter
            location: Location filter
            features: List of required features
            price_range: Price range filter
            min_rating: Minimum rating filter
            
        Returns:
            List of matching restaurants
        """
        results = []
        
        for restaurant in self._restaurants:
            # Check basic criteria using restaurant's matches_criteria method
            if not restaurant.matches_criteria(cuisine, location, features, price_range):
                continue
            
            # Check minimum rating
            if min_rating is not None and restaurant.rating < min_rating:
                continue
            
            results.append(restaurant)
        
        # Sort by rating descending
        results.sort(key=lambda r: r.rating, reverse=True)
        return results
    
    def get_restaurants_by_cuisine(self, cuisine: str) -> List[Restaurant]:
        """Get restaurants by cuisine type."""
        return self.search_restaurants(cuisine=cuisine)
    
    def get_restaurants_by_location(self, location: str) -> List[Restaurant]:
        """Get restaurants by location."""
        return self.search_restaurants(location=location)
    
    def get_featured_restaurants(self, feature: str) -> List[Restaurant]:
        """Get restaurants with specific feature."""
        return self.search_restaurants(features=[feature])

# Global restaurant loader instance
_restaurant_loader = None

def get_restaurant_loader() -> RestaurantLoader:
    """Get global restaurant loader instance."""
    global _restaurant_loader
    if _restaurant_loader is None:
        _restaurant_loader = RestaurantLoader()
    return _restaurant_loader
