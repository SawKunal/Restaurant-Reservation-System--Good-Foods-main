"""Reservation data model."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

@dataclass
class Reservation:
    """Reservation model for restaurant bookings."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    restaurant_id: str = ""
    customer_name: str = ""
    customer_phone: str = ""
    customer_email: str = ""
    party_size: int = 0
    date: str = ""  # YYYY-MM-DD format
    time: str = ""  # HH:MM format
    special_requests: str = ""
    status: str = "confirmed"  # confirmed, cancelled, completed
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def __post_init__(self):
        """Validate reservation data after initialization."""
        if self.party_size <= 0:
            raise ValueError("Party size must be positive")
        
        # Validate date format
        try:
            datetime.strptime(self.date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        
        # Validate time format
        try:
            datetime.strptime(self.time, "%H:%M")
        except ValueError:
            raise ValueError("Time must be in HH:MM format")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert reservation to dictionary."""
        return {
            'id': self.id,
            'restaurant_id': self.restaurant_id,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'customer_email': self.customer_email,
            'party_size': self.party_size,
            'date': self.date,
            'time': self.time,
            'special_requests': self.special_requests,
            'status': self.status,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Reservation':
        """Create reservation from dictionary."""
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            restaurant_id=data['restaurant_id'],
            customer_name=data['customer_name'],
            customer_phone=data['customer_phone'],
            customer_email=data['customer_email'],
            party_size=data['party_size'],
            date=data['date'],
            time=data['time'],
            special_requests=data.get('special_requests', ''),
            status=data.get('status', 'confirmed'),
            created_at=data.get('created_at', datetime.now().isoformat())
        )
    
    def get_datetime(self) -> datetime:
        """Get reservation datetime as datetime object."""
        return datetime.strptime(f"{self.date} {self.time}", "%Y-%m-%d %H:%M")
    
    def is_active(self) -> bool:
        """Check if reservation is active (not cancelled)."""
        return self.status != "cancelled"
    
    def is_past(self) -> bool:
        """Check if reservation is in the past."""
        return self.get_datetime() < datetime.now()
