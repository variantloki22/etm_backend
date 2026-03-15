from django.db import models

class TicketTransaction(models.Model):
    # ETM data fields
    category = models.CharField(max_length=50, help_text="Ticket Category (e.g. Adult, Child)")
    ticket_count = models.IntegerField(default=1, help_text="Number of tickets issued")
    latitude = models.FloatField(help_text="GPS Latitude")
    longitude = models.FloatField(help_text="GPS Longitude")
    timestamp = models.DateTimeField(help_text="Time of ticket issuance")
    route = models.CharField(max_length=100, help_text="Route identifier (e.g. 201A, 335E)")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ticket_count}x {self.category} on {self.route} at {self.timestamp}"
