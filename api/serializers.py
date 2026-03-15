from rest_framework import serializers
from .models import TicketTransaction

class TicketTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketTransaction
        fields = '__all__'
