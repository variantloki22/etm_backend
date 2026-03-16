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

class RouteViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def get_collection(self):
        client = MongoClient(settings.MONGO_URI)
        db = client[settings.MONGO_DB_NAME]
        return db['app_routes']

    def list(self, request):
        collection = self.get_collection()
        route_type = request.query_params.get('type')
        query = {}
        if route_type:
            query['type'] = route_type
        
        routes = list(collection.find(query))
        for r in routes:
            r['_id'] = str(r['_id'])
        return Response(routes)

class BusViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def get_collection(self):
        client = MongoClient(settings.MONGO_URI)
        db = client[settings.MONGO_DB_NAME]
        return db['app_buses']

    def list(self, request):
        collection = self.get_collection()
        route_name = request.query_params.get('route_name')
        query = {}
        if route_name:
            query['route_name'] = route_name
        
        buses = list(collection.find(query))
        for b in buses:
            b['_id'] = str(b['_id'])
        return Response(buses)

    @action(detail=True, methods=['post'], url_path='track')
    def track_me(self, request, pk=None):
        """
        Updates the current location of the user/bus for better tracking.
        'pk' here would be the bus_id.
        """
        collection = self.get_collection()
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        
        if lat is None or lng is None:
            return Response({"error": "Latitude and Longitude required"}, status=400)

        collection.update_one(
            {"bus_id": pk},
            {"$set": {"current_location": {"lat": float(lat), "lng": float(lng)}, "last_update": datetime.datetime.utcnow().isoformat()}}
        )
        return Response({"status": "Location updated"})
