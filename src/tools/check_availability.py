"""Check restaurant availability tool."""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
from src.tools.base_tool import BaseTool
from src.data.restaurant_loader import get_restaurant_loader
from src.models.reservation import Reservation
from src.config.settings import get_settings

class CheckAvailabilityTool(BaseTool):
    """Tool for checking restaurant availability on specific dates and times."""
    
    def __init__(self):
        self.settings = get_settings()
        self.reservations_file = self.settings.RESERVATION_DATA_FILE
    
    @property
    def name(self) -> str:
        return "check_availability"
    
    @property
    def description(self) -> str:
        return "Check if a restaurant has availability for a specific date, time, and party size. Returns available time slots if the exact time is not available."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "restaurant_id": {
                    "type": "string",
                    "description": "Restaurant ID to check availability for"
                },
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format"
                },
                "time": {
                    "type": "string",
                    "description": "Desired time in HH:MM format (24-hour)"
                },
                "party_size": {
                    "type": "integer",
                    "description": "Number of people in the party",
                    "minimum": 1
                }
            },
            "required": ["restaurant_id", "date", "time", "party_size"]
        }
    
    def load_reservations(self) -> List[Reservation]:
        """Load existing reservations from file."""
        try:
            if os.path.exists(self.reservations_file):
                with open(self.reservations_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [Reservation.from_dict(res) for res in data]
            return []
        except Exception:
            return []
    
    def get_restaurant_reservations(self, restaurant_id: str, date: str) -> List[Reservation]:
        """Get all active reservations for a restaurant on a specific date."""
        reservations = self.load_reservations()
        return [
            res for res in reservations 
            if res.restaurant_id == restaurant_id 
            and res.date == date 
            and res.is_active()
        ]
    
    def calculate_occupied_capacity(self, reservations: List[Reservation], check_time: str) -> int:
        """Calculate how many seats are occupied at a specific time."""
        occupied = 0
        check_datetime = datetime.strptime(check_time, "%H:%M")
        
        for reservation in reservations:
            res_time = datetime.strptime(reservation.time, "%H:%M")
            # Assume each reservation occupies the table for 2 hours
            end_time = res_time + timedelta(hours=2)
            
            # Check if the times overlap
            if res_time <= check_datetime < end_time:
                occupied += reservation.party_size
        
        return occupied
    
    def find_available_slots(self, restaurant_id: str, date: str, party_size: int) -> List[str]:
        """Find available time slots for the date."""
        restaurant_loader = get_restaurant_loader()
        restaurant = restaurant_loader.get_restaurant_by_id(restaurant_id)
        
        if not restaurant:
            return []
        
        reservations = self.get_restaurant_reservations(restaurant_id, date)
        available_slots = []
        
        # Check slots from 11:00 to 21:00 in 30-minute intervals
        current_time = datetime.strptime("11:00", "%H:%M")
        end_time = datetime.strptime("21:00", "%H:%M")
        
        while current_time <= end_time:
            time_str = current_time.strftime("%H:%M")
            occupied_capacity = self.calculate_occupied_capacity(reservations, time_str)
            
            if occupied_capacity + party_size <= restaurant.capacity:
                available_slots.append(time_str)
            
            current_time += timedelta(minutes=30)
        
        return available_slots
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute availability check."""
        try:
            # Validate parameters
            if not self.validate_parameters(**kwargs):
                return {
                    "success": False,
                    "message": "Missing required parameters",
                    "available": False
                }
            
            restaurant_id = kwargs["restaurant_id"]
            date = kwargs["date"]
            time = kwargs["time"]
            party_size = kwargs["party_size"]
            
            # Validate date format
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                return {
                    "success": False,
                    "message": "Invalid date format. Use YYYY-MM-DD",
                    "available": False
                }
            
            # Validate time format
            try:
                datetime.strptime(time, "%H:%M")
            except ValueError:
                return {
                    "success": False,
                    "message": "Invalid time format. Use HH:MM",
                    "available": False
                }
            
            # Check if date is in the past
            request_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            if request_datetime < datetime.now():
                return {
                    "success": False,
                    "message": "Cannot make reservations for past dates",
                    "available": False
                }
            
            # Get restaurant
            restaurant_loader = get_restaurant_loader()
            restaurant = restaurant_loader.get_restaurant_by_id(restaurant_id)
            
            if not restaurant:
                return {
                    "success": False,
                    "message": f"Restaurant with ID '{restaurant_id}' not found",
                    "available": False
                }
            
            # Check if party size exceeds restaurant capacity
            if party_size > restaurant.capacity:
                return {
                    "success": False,
                    "message": f"Party size ({party_size}) exceeds restaurant capacity ({restaurant.capacity})",
                    "available": False
                }
            
            # Get reservations for the date
            reservations = self.get_restaurant_reservations(restaurant_id, date)
            
            # Check availability at requested time
            occupied_capacity = self.calculate_occupied_capacity(reservations, time)
            available_capacity = restaurant.capacity - occupied_capacity
            
            is_available = available_capacity >= party_size
            
            if is_available:
                return {
                    "success": True,
                    "message": f"Table for {party_size} is available at {time} on {date}",
                    "available": True,
                    "restaurant_name": restaurant.name,
                    "requested_time": time,
                    "available_capacity": available_capacity
                }
            else:
                # Find alternative time slots
                available_slots = self.find_available_slots(restaurant_id, date, party_size)
                
                return {
                    "success": True,
                    "message": f"Requested time not available, but found {len(available_slots)} alternative slots",
                    "available": False,
                    "restaurant_name": restaurant.name,
                    "requested_time": time,
                    "alternative_slots": available_slots[:10],  # Limit to 10 alternatives
                    "available_capacity_at_requested_time": available_capacity
                }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error checking availability: {str(e)}",
                "available": False
            }
