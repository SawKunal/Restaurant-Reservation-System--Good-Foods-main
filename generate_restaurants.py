"""Generate sample restaurant data."""

import json
import random
from typing import List, Dict, Any

# Restaurant data templates
CUISINES = [
    "Italian", "Chinese", "Japanese", "Mexican", "Indian", "French", "Thai"
]

LOCATIONS = [
    "Downtown", "Midtown", "Uptown", "Westside", "Eastside", "Northside", 
    "Southside", "Financial District"
]

FEATURES = [
    "romantic", "family-friendly", "outdoor-seating", "live-music", "rooftop",
    "private-dining", "vegan-options", "gluten-free", "bar", "wine-bar",
    "business-friendly", "pet-friendly", "wheelchair-accessible", "parking",
    "takeout", "delivery", "catering", "late-night", "brunch", "buffet"
]

SPECIAL_OCCASIONS = [
    "birthday", "anniversary", "business-meeting", "date-night", "family-gathering",
    "celebration", "graduation", "wedding-party", "corporate-event", "holiday-party"
]

PRICE_RANGES = ["$20", "$30", "$40", "$50"]

def generate_opening_hours() -> Dict[str, str]:
    """Generate realistic opening hours."""
    weekday_hours = ["9:00-22:00", "10:00-23:00", "11:00-22:30", "8:00-21:00"]
    weekend_hours = ["9:00-23:00", "10:00-24:00", "11:00-23:30", "8:00-22:00"]
    
    return {
        "monday": random.choice(weekday_hours),
        "tuesday": random.choice(weekday_hours),
        "wednesday": random.choice(weekday_hours),
        "thursday": random.choice(weekday_hours),
        "friday": random.choice(weekend_hours),
        "saturday": random.choice(weekend_hours),
        "sunday": random.choice(weekend_hours)
    }

def generate_restaurant_name(cuisine: str, location: str) -> str:
    """Generate a restaurant name based on cuisine and location."""
    
    cuisine_prefixes = {
        "Italian": ["Bella", "Casa", "Villa", "Mama", "Tony's", "Giuseppe's"],
        "Chinese": ["Golden", "Dragon", "Jade", "Phoenix", "Lucky", "Ming's"],
        "Japanese": ["Sakura", "Tokyo", "Zen", "Koi", "Bamboo", "Sushi"],
        "Mexican": ["El", "La", "Casa", "Taco", "Fiesta", "Cantina"],
        "Indian": ["Taj", "Spice", "Curry", "Bombay", "Delhi", "Rajah"],
        "French": ["Le", "La", "Café", "Bistro", "Chez", "Boulangerie"],
        "Thai": ["Thai", "Siam", "Bangkok", "Lotus", "Basil", "Coconut"],
    }
    
    suffixes = ["Kitchen", "Bistro", "Grill", "House", "Garden", "Corner", "Place", 
                "Room", "Table", "Spot", "Bar", "Cafe", "Restaurant"]
    
    if cuisine in cuisine_prefixes:
        prefix = random.choice(cuisine_prefixes[cuisine])
    else:
        prefix = location
    
    suffix = random.choice(suffixes)
    
    return f"{prefix} {suffix}"

def generate_description(cuisine: str, features: List[str]) -> str:
    """Generate restaurant description."""
    descriptions = [
        f"Authentic {cuisine.lower()} cuisine served in a welcoming atmosphere.",
        f"Experience the finest {cuisine.lower()} flavors with our traditional recipes.",
        f"A modern take on classic {cuisine.lower()} dishes with fresh ingredients.",
        f"Family-owned restaurant serving delicious {cuisine.lower()} food since 1995.",
        f"Upscale {cuisine.lower()} dining with an extensive wine selection."
    ]
    
    base_desc = random.choice(descriptions)
    
    if "romantic" in features:
        base_desc += " Perfect for intimate dining and special occasions."
    if "family-friendly" in features:
        base_desc += " Great for families with children."
    if "outdoor-seating" in features:
        base_desc += " Enjoy dining on our beautiful patio."
    
    return base_desc

def generate_restaurants(count: int = 100) -> List[Dict[str, Any]]:
    """Generate sample restaurant data."""
    restaurants = []
    
    for i in range(count):
        cuisine = random.choice(CUISINES)
        location = random.choice(LOCATIONS)
        name = generate_restaurant_name(cuisine, location)
        
        # Select random features (2-6 features per restaurant)
        restaurant_features = random.sample(FEATURES, random.randint(2, 6))
        
        # Select random special occasions (1-4 occasions per restaurant)
        occasions = random.sample(SPECIAL_OCCASIONS, random.randint(1, 4))
        
        email_clean = name.lower().replace(" ", "").replace("'", "")
        restaurant = {
            "id": f"rest_{i+1:03d}",
            "name": name,
            "cuisine_type": cuisine,
            "location": location,
            "address": f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Pine', 'Elm', 'First', 'Second', 'Broadway', 'Center'])} St, {location}",
            "phone": f"({random.randint(200, 999)}) {random.randint(100, 999)}-{random.randint(1000, 9999)}",
            "email": f"info@{email_clean}.com",
            "capacity": random.choice([20, 30, 40, 50, 60, 80, 100, 120, 150, 200]),
            "price_range": random.choice(PRICE_RANGES),
            "rating": round(random.uniform(3.5, 5.0), 1),
            "description": generate_description(cuisine, restaurant_features),
            "features": restaurant_features,
            "opening_hours": generate_opening_hours(),
            "special_occasions": occasions
        }
        
        restaurants.append(restaurant)
    
    return restaurants

def main():
    """Generate and save restaurant data."""
    print("Generating 100 sample restaurants...")
    restaurants = generate_restaurants(100)
    
    # Save to JSON file
    import os
    output_dir = "../src/data/"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "restaurants.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(restaurants, f, indent=2, ensure_ascii=False)
    
    print(f"Generated {len(restaurants)} restaurants and saved to {output_file}")
    
    # Print sample data
    print("\nSample restaurants:")
    for i, restaurant in enumerate(restaurants[:5]):
        print(f"{i+1}. {restaurant['name']} - {restaurant['cuisine_type']} - {restaurant['location']}")

if __name__ == "__main__":
    main()
