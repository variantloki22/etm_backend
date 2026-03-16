import os
import sys
import django
from pymongo import MongoClient
import datetime

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'etm_backend.settings')
django.setup()

from django.conf import settings

def init_db():
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB_NAME]
    
    # 1. Clear existing collections if any (caution)
    # db['app_routes'].drop()
    # db['app_buses'].drop()
    
    # 2. Define Routes (3 routes)
    routes_data = [
        {
            "name": "Route V1 - Village Connect",
            "type": "Village",
            "description": "Connecting Marakkanam to ECR villages."
        },
        {
            "name": "Route V2 - Rural Express",
            "type": "Village",
            "description": "Deep rural service for Kovalam stretch."
        },
        {
            "name": "Route C1 - City Line",
            "type": "Chennai City",
            "description": "High-frequency service in T.Nagar - CMBT."
        }
    ]
    
    # 3. Define Buses (3 for each route)
    buses_data = []
    
    # Common Stops for Village 1
    v1_stops = [
        {"name": "Marakkanam", "lat": 12.19, "lng": 79.94},
        {"name": "Kadappakkam", "lat": 12.25, "lng": 79.98},
        {"name": "Pudupattinam", "lat": 12.50, "lng": 80.15},
        {"name": "Kelambakkam", "lat": 12.78, "lng": 80.22}
    ]
    
    # Common Stops for Village 2
    v2_stops = [
        {"name": "Kovalam", "lat": 12.79, "lng": 80.24},
        {"name": "Muttukadu", "lat": 12.82, "lng": 80.24},
        {"name": "Akkarai", "lat": 12.88, "lng": 80.24},
        {"name": "Sholinganallur", "lat": 12.90, "lng": 80.22}
    ]
    
    # Common Stops for City 1
    c1_stops = [
        {"name": "T.Nagar", "lat": 13.04, "lng": 80.23},
        {"name": "Nandanam", "lat": 13.03, "lng": 80.24},
        {"name": "Saidapet", "lat": 13.02, "lng": 80.22},
        {"name": "Guindy", "lat": 13.00, "lng": 80.22},
        {"name": "CMBT", "lat": 13.06, "lng": 80.20}
    ]
    
    for i in range(1, 4):
        buses_data.append({
            "bus_id": f"V1-{i:02d}",
            "route_name": "Route V1 - Village Connect",
            "capacity": 55,
            "stops": v1_stops,
            "current_location": {"lat": 12.19, "lng": 79.94}
        })
        buses_data.append({
            "bus_id": f"V2-{i:02d}",
            "route_name": "Route V2 - Rural Express",
            "capacity": 55,
            "stops": v2_stops,
            "current_location": {"lat": 12.79, "lng": 80.24}
        })
        buses_data.append({
            "bus_id": f"C1-{i:02d}",
            "route_name": "Route C1 - City Line",
            "capacity": 70,
            "stops": c1_stops,
            "current_location": {"lat": 13.04, "lng": 80.23}
        })

    # Insert Data
    db['app_routes'].delete_many({}) # Clear first
    db['app_routes'].insert_many(routes_data)
    
    db['app_buses'].delete_many({}) # Clear first
    db['app_buses'].insert_many(buses_data)
    
    print(f"Successfully initialized DB with {len(routes_data)} routes and {len(buses_data)} buses.")

if __name__ == "__main__":
    init_db()
