from rest_framework import viewsets, status
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.conf import settings
from pymongo import MongoClient
import datetime
from django.utils import timezone

# We don't use the Django ORM for TicketTransaction anymore because djongo was problematic
# We will use PyMongo directly in the views.

class TicketTransactionViewSet(viewsets.ViewSet):
    """
    API endpoint that allows TicketTransactions to be viewed or created via PyMongo.
    """
    permission_classes = [permissions.AllowAny]

    def get_collection(self):
        client = MongoClient(settings.MONGO_URI)
        db = client[settings.MONGO_DB_NAME]
        return db['ticket_transactions']

    def list(self, request):
        collection = self.get_collection()
        # Fetch latest 50 transactions
        transactions = list(collection.find().sort("timestamp", -1).limit(50))
        # Convert ObjectId to string for JSON serialization
        for t in transactions:
            t['_id'] = str(t['_id'])
        return Response(transactions)

    def create(self, request):
        collection = self.get_collection()
        data = request.data
        
        # Validate minimal requirements
        required_fields = ['category', 'ticket_count', 'latitude', 'longitude', 'route', 'from_location', 'to_location']
        for field in required_fields:
            if field not in data:
                return Response({"error": f"Missing field: {field}"}, status=status.HTTP_400_BAD_REQUEST)
        
        document = {
            "category": data['category'],
            "ticket_count": int(data['ticket_count']),
            "latitude": float(data['latitude']),
            "longitude": float(data['longitude']),
            "route": data['route'],
            "from_location": data['from_location'],
            "to_location": data['to_location'],
            "timestamp": data.get('timestamp', datetime.datetime.utcnow().isoformat()),
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        
        
        result = collection.insert_one(document)
        document['_id'] = str(result.inserted_id)
        
        return Response(document, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='crowd/(?P<route_name>[^/.]+)')
    def route_crowd(self, request, route_name=None):
        """
        Calculates the crowd status for a specific route based on 
        tickets sold in the last 2 hours.
        """
        collection = self.get_collection()
        
        # Calculate time 24 hours ago (increased for better simulation/testing)
        two_hours_ago = (datetime.datetime.utcnow() - datetime.timedelta(hours=24)).isoformat()
        
        # Query for tickets on this route in the last 2 hours
        query = {
            "route": route_name,
            "timestamp": {"$gte": two_hours_ago}
        }
        
        tickets = list(collection.find(query))
        total_passengers = sum(int(t.get('ticket_count', 1)) for t in tickets)
        
        # Determine crowd level
        # Thresholds: Low < 20, Medium 20-50, High > 50
        crowd_status = "Low"
        if total_passengers > 50:
            crowd_status = "High"
        elif total_passengers > 20:
            crowd_status = "Medium"
            
        return Response({
            "route": route_name,
            "passenger_count": total_passengers,
            "crowd_status": crowd_status,
            "window_hours": 2,
            "checked_at": datetime.datetime.utcnow().isoformat()
        })

class BusTrackingViewSet(viewsets.ViewSet):
    """
    API endpoint for tracking multiple buses per route.
    Uses a separate database 'namma_bus_tracking'.
    """
    permission_classes = [permissions.AllowAny]

    def get_collection(self):
        client = MongoClient(settings.MONGO_URI)
        db = client[settings.MONGO_TRACKING_DB_NAME]
        return db['active_buses']

    def _initialize_buses_if_needed(self, collection):
        if collection.count_documents({}) == 0:
            routes = ['335E', '201A', '500C', 'G3', 'V-335E']
            buses = []
            for route in routes:
                for i in range(1, 4):
                    buses.append({
                        "bus_id": f"{route}-{i}",
                        "route": route,
                        "instance": i,
                        "latitude": 12.9716, # Default Bangalore
                        "longitude": 77.5946,
                        "is_tracked": False,
                        "last_updated": datetime.datetime.utcnow().isoformat(),
                        "passenger_count": 0
                    })
            collection.insert_many(buses)

    def list(self, request):
        collection = self.get_collection()
        self._initialize_buses_if_needed(collection)
        
        buses = list(collection.find())
        for b in buses:
            b['_id'] = str(b['_id'])
        return Response(buses)

    @action(detail=False, methods=['post'], url_path='update-location')
    def update_location(self, request):
        bus_id = request.data.get('bus_id')
        lat = request.data.get('latitude')
        lng = request.data.get('longitude')
        
        if not bus_id or lat is None or lng is None:
            return Response({"error": "Missing bus_id, latitude or longitude"}, status=status.HTTP_400_BAD_REQUEST)
            
        collection = self.get_collection()
        result = collection.update_one(
            {"bus_id": bus_id},
            {"$set": {
                "latitude": float(lat),
                "longitude": float(lng),
                "last_updated": datetime.datetime.utcnow().isoformat(),
                "is_tracked": True
            }}
        )
        
        if result.matched_count == 0:
            return Response({"error": "Bus not found"}, status=status.HTTP_404_NOT_FOUND)
            
        return Response({"status": "success"})

    @action(detail=False, methods=['post'], url_path='toggle-tracking')
    def toggle_tracking(self, request):
        bus_id = request.data.get('bus_id')
        is_tracked = request.data.get('is_tracked', False)
        
        if not bus_id:
            return Response({"error": "Missing bus_id"}, status=status.HTTP_400_BAD_REQUEST)
            
        collection = self.get_collection()
        collection.update_one(
            {"bus_id": bus_id},
            {"$set": {"is_tracked": is_tracked}}
        )
        
        return Response({"status": "success", "is_tracked": is_tracked})

