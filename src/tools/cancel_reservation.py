"""Cancel reservation tool."""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from src.tools.base_tool import BaseTool
from src.data.restaurant_loader import get_restaurant_loader
from src.models.reservation import Reservation
from src.config.settings import get_settings

class CancelReservationTool(BaseTool):
    """Tool for canceling restaurant reservations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.reservations_file = self.settings.RESERVATION_DATA_FILE
    
    @property
    def name(self) -> str:
        return "cancel_reservation"
    
    @property
    def description(self) -> str:
        return "Cancel an existing reservation using the reservation ID, customer name, or customer phone number."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "reservation_id": {
                    "type": "string",
                    "description": "Reservation ID to cancel (if known)"
                },
                "customer_name": {
                    "type": "string",
                    "description": "Customer name associated with the reservation"
                },
                "customer_phone": {
                    "type": "string",
                    "description": "Customer phone number associated with the reservation"
                },
                "customer_email": {
                    "type": "string",
                    "description": "Customer email associated with the reservation"
                }
            },
            "required": [],
            "anyOf": [
                {"required": ["reservation_id"]},
                {"required": ["customer_name"]},
                {"required": ["customer_phone"]},
                {"required": ["customer_email"]}
            ]
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
    
    def find_reservation(self, reservation_id: Optional[str] = None, 
                        customer_name: Optional[str] = None,
                        customer_phone: Optional[str] = None,
                        customer_email: Optional[str] = None) -> Optional[Reservation]:
        """Find reservation by various criteria."""
        reservations = self.load_reservations()
        
        # Filter active reservations only
        active_reservations = [res for res in reservations if res.is_active()]
        
        if reservation_id:
            for reservation in active_reservations:
                if reservation.id == reservation_id:
                    return reservation
        
        if customer_name:
            matches = [res for res in active_reservations 
                      if res.customer_name.lower() == customer_name.lower()]
            if matches:
                return matches[0]  # Return first match
        
        if customer_phone:
            matches = [res for res in active_reservations 
                      if res.customer_phone == customer_phone]
            if matches:
                return matches[0]  # Return first match
        
        if customer_email:
            matches = [res for res in active_reservations 
                      if res.customer_email.lower() == customer_email.lower()]
            if matches:
                return matches[0]  # Return first match
        
        return None
    
    def find_multiple_reservations(self, customer_name: Optional[str] = None,
                                  customer_phone: Optional[str] = None,
                                  customer_email: Optional[str] = None) -> List[Reservation]:
        """Find multiple reservations for a customer."""
        reservations = self.load_reservations()
        active_reservations = [res for res in reservations if res.is_active()]
        
        matches = []
        
        if customer_name:
            matches.extend([res for res in active_reservations 
                           if res.customer_name.lower() == customer_name.lower()])
        
        if customer_phone:
            matches.extend([res for res in active_reservations 
                           if res.customer_phone == customer_phone])
        
        if customer_email:
            matches.extend([res for res in active_reservations 
                           if res.customer_email.lower() == customer_email.lower()])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_matches = []
        for reservation in matches:
            if reservation.id not in seen:
                seen.add(reservation.id)
                unique_matches.append(reservation)
        
        return unique_matches
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute reservation cancellation."""
        try:
            reservation_id = kwargs.get("reservation_id")
            customer_name = kwargs.get("customer_name")
            customer_phone = kwargs.get("customer_phone")
            customer_email = kwargs.get("customer_email")
            
            # Check if at least one identifier is provided
            if not any([reservation_id, customer_name, customer_phone, customer_email]):
                return {
                    "success": False,
                    "message": "Please provide at least one identifier: reservation ID, customer name, phone, or email"
                }
            
            # Find reservation(s)
            if reservation_id:
                # Direct lookup by reservation ID
                reservation = self.find_reservation(reservation_id=reservation_id)
                if not reservation:
                    return {
                        "success": False,
                        "message": f"No active reservation found with ID: {reservation_id}"
                    }
            else:
                # Find by customer information
                reservations_found = self.find_multiple_reservations(
                    customer_name=customer_name,
                    customer_phone=customer_phone,
                    customer_email=customer_email
                )
                
                if not reservations_found:
                    return {
                        "success": False,
                        "message": "No active reservations found with the provided information"
                    }
                
                if len(reservations_found) == 1:
                    reservation = reservations_found[0]
                else:
                    # Multiple reservations found - return them for user selection
                    restaurant_loader = get_restaurant_loader()
                    reservation_list = []
                    
                    for res in reservations_found:
                        restaurant = restaurant_loader.get_restaurant_by_id(res.restaurant_id)
                        restaurant_name = restaurant.name if restaurant else "Unknown Restaurant"
                        
                        reservation_list.append({
                            "reservation_id": res.id,
                            "restaurant_name": restaurant_name,
                            "date": res.date,
                            "time": res.time,
                            "party_size": res.party_size
                        })
                    
                    return {
                        "success": False,
                        "message": f"Multiple reservations found ({len(reservations_found)}). Please specify which one to cancel using the reservation ID.",
                        "reservations": reservation_list
                    }
            
            # Get restaurant details for confirmation
            restaurant_loader = get_restaurant_loader()
            restaurant = restaurant_loader.get_restaurant_by_id(reservation.restaurant_id)
            restaurant_name = restaurant.name if restaurant else "Unknown Restaurant"
            
            # Cancel the reservation
            all_reservations = self.load_reservations()
            for res in all_reservations:
                if res.id == reservation.id:
                    res.status = "cancelled"
                    break
            
            # Save updated reservations
            self.save_reservations(all_reservations)
            
            return {
                "success": True,
                "message": f"Reservation successfully cancelled for {reservation.customer_name}",
                "cancelled_reservation": {
                    "reservation_id": reservation.id,
                    "restaurant_name": restaurant_name,
                    "customer_name": reservation.customer_name,
                    "date": reservation.date,
                    "time": reservation.time,
                    "party_size": reservation.party_size,
                    "status": "cancelled"
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error cancelling reservation: {str(e)}"
            }
