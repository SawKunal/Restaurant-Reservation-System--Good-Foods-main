"""Reservation data management for the restaurant AI agent."""

import json
import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from src.models.reservation import Reservation
from src.config.settings import get_settings
from src.utils.logger import data_logger

class ReservationManager:
    """Handles loading and managing reservation data."""
    
    def __init__(self):
        """Initialize reservation manager."""
        self.settings = get_settings()
        self.data_file = self.settings.RESERVATION_DATA_FILE
        self._reservations: List[Reservation] = []
        self.load_reservations()
    
    def load_reservations(self):
        """Load reservations from JSON file."""
        try:
            data_logger.log_data_operation("LOAD", "reservations", details={"file": self.data_file})
            
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._reservations = [Reservation.from_dict(reservation) for reservation in data]
                
                data_logger.log_data_operation("LOAD_SUCCESS", "reservations", 
                                             details={"count": len(self._reservations), "file": self.data_file})
            else:
                data_logger.logger.info(f"📝 RESERVATIONS: No existing reservation file found, starting fresh")
                self._reservations = []
        except Exception as e:
            data_logger.log_error(e, "load_reservations", {"file": self.data_file})
            self._reservations = []
    
    def save_reservations(self):
        """Save reservations to JSON file."""
        try:
            data_logger.log_data_operation("SAVE", "reservations", details={"count": len(self._reservations)})
            
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                data = [reservation.to_dict() for reservation in self._reservations]
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            data_logger.log_data_operation("SAVE_SUCCESS", "reservations", 
                                         details={"count": len(self._reservations), "file": self.data_file})
        except Exception as e:
            data_logger.log_error(e, "save_reservations", {"file": self.data_file})
    
    def get_all_reservations(self) -> List[Reservation]:
        """Get all reservations."""
        return self._reservations.copy()
    
    def get_active_reservations(self) -> List[Reservation]:
        """Get active (non-cancelled) reservations."""
        return [r for r in self._reservations if r.status != "cancelled"]
    
    def get_reservation_by_id(self, reservation_id: str) -> Optional[Reservation]:
        """Get reservation by ID."""
        for reservation in self._reservations:
            if reservation.reservation_id == reservation_id:
                return reservation
        return None
    
    def find_reservations_by_customer(self, customer_name: str, 
                                    customer_phone: Optional[str] = None) -> List[Reservation]:
        """Find reservations by customer name and optionally phone."""
        results = []
        for reservation in self._reservations:
            # Match by name (case insensitive)
            if customer_name.lower() in reservation.customer_name.lower():
                # If phone provided, also match phone
                if customer_phone is None or customer_phone in reservation.customer_phone:
                    results.append(reservation)
        return results
    
    def find_reservations_by_restaurant(self, restaurant_id: str, 
                                      date_str: Optional[str] = None) -> List[Reservation]:
        """Find reservations by restaurant and optionally date."""
        results = []
        for reservation in self._reservations:
            if reservation.restaurant_id == restaurant_id:
                if date_str is None or reservation.reservation_date == date_str:
                    results.append(reservation)
        return results
    
    def create_reservation(self, restaurant_id: str, restaurant_name: str,
                          reservation_date: str, reservation_time: str,
                          party_size: int, customer_name: str,
                          customer_phone: str, customer_email: str) -> Reservation:
        """Create a new reservation."""
        # Generate unique reservation ID
        reservation_id = f"res_{uuid.uuid4().hex[:8]}"
        
        # Create reservation object
        reservation = Reservation(
            reservation_id=reservation_id,
            restaurant_id=restaurant_id,
            restaurant_name=restaurant_name,
            reservation_date=reservation_date,
            reservation_time=reservation_time,
            party_size=party_size,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            status="confirmed",
            created_at=datetime.now().isoformat()
        )
        
        # Add to reservations list
        self._reservations.append(reservation)
        
        # Save to file
        self.save_reservations()
        
        data_logger.log_data_operation("CREATE", "reservation", 
                                     details={"reservation_id": reservation_id, "restaurant": restaurant_name})
        
        return reservation
    
    def cancel_reservation(self, reservation_id: str) -> bool:
        """Cancel a reservation by ID."""
        for reservation in self._reservations:
            if reservation.reservation_id == reservation_id:
                reservation.status = "cancelled"
                reservation.updated_at = datetime.now().isoformat()
                
                # Save changes
                self.save_reservations()
                
                data_logger.log_data_operation("CANCEL", "reservation", 
                                             details={"reservation_id": reservation_id})
                return True
        
        return False
    
    def cancel_reservation_by_customer(self, customer_name: str, 
                                     restaurant_name: str = None,
                                     reservation_date: str = None) -> List[str]:
        """Cancel reservations by customer details. Returns list of cancelled reservation IDs."""
        cancelled_ids = []
        
        for reservation in self._reservations:
            if (reservation.status != "cancelled" and 
                customer_name.lower() in reservation.customer_name.lower()):
                
                # Additional filters if provided
                if restaurant_name and restaurant_name.lower() not in reservation.restaurant_name.lower():
                    continue
                if reservation_date and reservation.reservation_date != reservation_date:
                    continue
                
                # Cancel this reservation
                reservation.status = "cancelled"
                reservation.updated_at = datetime.now().isoformat()
                cancelled_ids.append(reservation.reservation_id)
        
        if cancelled_ids:
            self.save_reservations()
            data_logger.log_data_operation("BULK_CANCEL", "reservations", 
                                         details={"cancelled_count": len(cancelled_ids)})
        
        return cancelled_ids
    
    def update_reservation(self, reservation_id: str, **updates) -> bool:
        """Update a reservation with new details."""
        for reservation in self._reservations:
            if reservation.reservation_id == reservation_id:
                # Update fields
                for field, value in updates.items():
                    if hasattr(reservation, field):
                        setattr(reservation, field, value)
                
                reservation.updated_at = datetime.now().isoformat()
                
                # Save changes
                self.save_reservations()
                
                data_logger.log_data_operation("UPDATE", "reservation", 
                                             details={"reservation_id": reservation_id, "updates": list(updates.keys())})
                return True
        
        return False

# Global reservation manager instance
_reservation_manager = None

def get_reservation_manager() -> ReservationManager:
    """Get global reservation manager instance."""
    global _reservation_manager
    if _reservation_manager is None:
        _reservation_manager = ReservationManager()
    return _reservation_manager
