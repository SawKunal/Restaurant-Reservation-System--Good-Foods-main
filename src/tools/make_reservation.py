"""Make reservation tool."""

import json
import os
from datetime import datetime
from typing import Dict, Any, List
from src.tools.base_tool import BaseTool
from src.data.restaurant_loader import get_restaurant_loader
from src.models.reservation import Reservation
from src.config.settings import get_settings

class MakeReservationTool(BaseTool):
    """Tool for making restaurant reservations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.reservations_file = self.settings.RESERVATION_DATA_FILE
    
    @property
    def name(self) -> str:
        return "make_reservation"
    
    @property
    def description(self) -> str:
        return "Make a reservation at a restaurant for a specific date, time, and party size. Requires customer contact information."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "restaurant_id": {
                    "type": "string",
                    "description": "Restaurant ID to make reservation at"
                },
                "customer_name": {
                    "type": "string",
                    "description": "Customer's full name"
                },
                "customer_phone": {
                    "type": "string",
                    "description": "Customer's phone number"
                },
                "customer_email": {
                    "type": "string",
                    "description": "Customer's email address"
                },
                "date": {
                    "type": "string",
                    "description": "Reservation date in YYYY-MM-DD format"
                },
                "time": {
                    "type": "string",
                    "description": "Reservation time in HH:MM format (24-hour)"
                },
                "party_size": {
                    "type": "integer",
                    "description": "Number of people in the party",
                    "minimum": 1
                },
                "special_requests": {
                    "type": "string",
                    "description": "Any special requests or notes (optional)"
                }
            },
            "required": ["restaurant_id", "customer_name", "customer_phone", "customer_email", "date", "time", "party_size"]
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
    
    def save_reservations(self, reservations: List[Reservation]):
        """Save reservations to file."""
        try:
            os.makedirs(os.path.dirname(self.reservations_file), exist_ok=True)
            data = [reservation.to_dict() for reservation in reservations]
            with open(self.reservations_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"Failed to save reservations: {str(e)}")
    
    def check_availability_for_reservation(self, restaurant_id: str, date: str, time: str, party_size: int) -> tuple[bool, str]:
        """Check if the reservation can be made."""
        # Get restaurant
        restaurant_loader = get_restaurant_loader()
        restaurant = restaurant_loader.get_restaurant_by_id(restaurant_id)
        
        if not restaurant:
            return False, f"Restaurant with ID '{restaurant_id}' not found"
        
        # Check if party size exceeds restaurant capacity
        if party_size > restaurant.capacity:
            return False, f"Party size ({party_size}) exceeds restaurant capacity ({restaurant.capacity})"
        
        # Get existing reservations for the date
        reservations = self.load_reservations()
        restaurant_reservations = [
            res for res in reservations 
            if res.restaurant_id == restaurant_id 
            and res.date == date 
            and res.is_active()
        ]
        
        # Calculate occupied capacity at the requested time
        occupied = 0
        request_datetime = datetime.strptime(time, "%H:%M")
        
        for reservation in restaurant_reservations:
            res_time = datetime.strptime(reservation.time, "%H:%M")
            # Assume each reservation occupies the table for 2 hours
            from datetime import timedelta
            end_time = res_time + timedelta(hours=2)
            
            # Check if the times overlap
            if res_time <= request_datetime < end_time:
                occupied += reservation.party_size
        
        available_capacity = restaurant.capacity - occupied
        
        if available_capacity >= party_size:
            return True, "Available"
        else:
            return False, f"Not enough capacity. Available: {available_capacity}, Requested: {party_size}"
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute reservation creation."""
        try:
            # Validate parameters
            if not self.validate_parameters(**kwargs):
                return {
                    "success": False,
                    "message": "Missing required parameters"
                }
            
            restaurant_id = kwargs["restaurant_id"]
            customer_name = kwargs["customer_name"]
            customer_phone = kwargs["customer_phone"]
            customer_email = kwargs["customer_email"]
            date = kwargs["date"]
            time = kwargs["time"]
            party_size = kwargs["party_size"]
            special_requests = kwargs.get("special_requests", "")
            
            # Validate date format
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                return {
                    "success": False,
                    "message": "Invalid date format. Use YYYY-MM-DD"
                }
            
            # Validate time format
            try:
                datetime.strptime(time, "%H:%M")
            except ValueError:
                return {
                    "success": False,
                    "message": "Invalid time format. Use HH:MM"
                }
            
            # Check if date is in the past
            request_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            if request_datetime < datetime.now():
                return {
                    "success": False,
                    "message": "Cannot make reservations for past dates"
                }
            
            # Validate email format (basic validation)
            if "@" not in customer_email or "." not in customer_email:
                return {
                    "success": False,
                    "message": "Invalid email format"
                }
            
            # Check availability
            is_available, availability_message = self.check_availability_for_reservation(
                restaurant_id, date, time, party_size
            )
            
            if not is_available:
                return {
                    "success": False,
                    "message": f"Reservation cannot be made: {availability_message}"
                }
            
            # Get restaurant details
            restaurant_loader = get_restaurant_loader()
            restaurant = restaurant_loader.get_restaurant_by_id(restaurant_id)
            
            # Create reservation
            reservation = Reservation(
                restaurant_id=restaurant_id,
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_email=customer_email,
                party_size=party_size,
                date=date,
                time=time,
                special_requests=special_requests,
                status="confirmed"
            )
            
            # Load existing reservations and add the new one
            reservations = self.load_reservations()
            reservations.append(reservation)
            
            # Save updated reservations
            self.save_reservations(reservations)
            
            return {
                "success": True,
                "message": f"Reservation confirmed for {customer_name}",
                "reservation": {
                    "reservation_id": reservation.id,
                    "restaurant_name": restaurant.name,
                    "customer_name": customer_name,
                    "date": date,
                    "time": time,
                    "party_size": party_size,
                    "special_requests": special_requests,
                    "restaurant_address": restaurant.address,
                    "restaurant_phone": restaurant.phone,
                    "status": "confirmed"
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error making reservation: {str(e)}"
            }
