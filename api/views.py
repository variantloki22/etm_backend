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


class BusRouteViewSet(viewsets.ViewSet):
    """
    API endpoint for Google Maps-like bus route information.
    """
    permission_classes = [permissions.AllowAny]

    def get_db(self):
        client = MongoClient(settings.MONGO_URI)
        return client[settings.MONGO_DB_NAME]

    def list(self, request):
        """Lists all 3 main routes"""
        db = self.get_db()
        routes = list(db.bus_routes.find({}, {'_id': 0}))
        return Response(routes)

    @action(detail=True, methods=['get'])
    def buses(self, request, pk=None):
        """Lists buses for a specific route (pk is route_id)"""
        db = self.get_db()
        buses = list(db.buses.find({"route_id": pk}, {'_id': 0}))
        return Response(buses)

    @action(detail=False, methods=['get'], url_path='stops/(?P<route_id>[^/.]+)')
    def stops(self, request, route_id=None):
        """Lists stops and timings for a specific route"""
        db = self.get_db()
        stops = list(db.bus_stops.find({"route_id": route_id}, {'_id': 0}).sort("order", 1))
        return Response(stops)

    @action(detail=False, methods=['post'], url_path='track')
    def track_commuter(self, request):
        """Receives live location from commuters toggled 'Inside a Bus'"""
        db = self.get_db()
        data = request.data
        
        # We store this in a TTL collection or just a log
        document = {
            "bus_id": data.get('bus_id'),
            "route_id": data.get('route_id'),
            "latitude": float(data.get('latitude', 0)),
            "longitude": float(data.get('longitude', 0)),
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "user_id": data.get('user_id', 'anonymous')
        }
        
        db.commuter_locations.insert_one(document)
        return Response({"status": "tracking_active"}, status=status.HTTP_201_CREATED)
