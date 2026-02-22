"""Restaurant data model."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

@dataclass
class Restaurant:
    """Restaurant model with all necessary information."""
    
    id: str
    name: str
    cuisine_type: str
    location: str
    address: str
    phone: str
    email: str
    capacity: int
    price_range: str  # $, $$, $$$, $$$$
    rating: float
    description: str
    features: List[str] = field(default_factory=list)  # ['romantic', 'family-friendly', 'outdoor-seating', etc.]
    opening_hours: Dict[str, str] = field(default_factory=dict)  # {'monday': '9:00-22:00', ...}
    special_occasions: List[str] = field(default_factory=list)  # ['birthday', 'anniversary', 'business']
    
    def __post_init__(self):
        """Validate restaurant data after initialization."""
        if self.rating < 0 or self.rating > 5:
            raise ValueError("Rating must be between 0 and 5")
        if self.capacity <= 0:
            raise ValueError("Capacity must be positive")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert restaurant to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'cuisine_type': self.cuisine_type,
            'location': self.location,
            'address': self.address,
            'phone': self.phone,
            'email': self.email,
            'capacity': self.capacity,
            'price_range': self.price_range,
            'rating': self.rating,
            'description': self.description,
            'features': self.features,
            'opening_hours': self.opening_hours,
            'special_occasions': self.special_occasions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Restaurant':
        """Create restaurant from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            cuisine_type=data['cuisine_type'],
            location=data['location'],
            address=data['address'],
            phone=data['phone'],
            email=data['email'],
            capacity=data['capacity'],
            price_range=data['price_range'],
            rating=data['rating'],
            description=data['description'],
            features=data.get('features', []),
            opening_hours=data.get('opening_hours', {}),
            special_occasions=data.get('special_occasions', [])
        )
    
    def matches_criteria(self, cuisine: Optional[str] = None, 
                        location: Optional[str] = None,
                        features: Optional[List[str]] = None,
                        price_range: Optional[str] = None) -> bool:
        """Check if restaurant matches search criteria."""
        if cuisine and cuisine.lower() not in self.cuisine_type.lower():
            return False
        
        if location and location.lower() not in self.location.lower():
            return False
        
        if features:
            restaurant_features_lower = [f.lower() for f in self.features]
            for feature in features:
                if feature.lower() not in restaurant_features_lower:
                    return False
        
        if price_range and price_range != self.price_range:
            return False
        
        return True
