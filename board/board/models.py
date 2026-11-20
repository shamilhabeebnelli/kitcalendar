from django.db import models
from django.conf import settings
from django.db.models import Q, F

class Equipment(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True, max_length=1000)
    active = models.BooleanField(default=True)
    # Every mutation locks this row with a write, including SQLite transactions.
    revision = models.PositiveIntegerField(default=0)
    class Meta:
        ordering = ["name"]
    def __str__(self):
        return self.name

class Reservation(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.PROTECT)
    borrower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    start = models.DateField()
    end = models.DateField()
    purpose = models.CharField(max_length=240)
    status = models.CharField(max_length=12, choices=[(x, x.title()) for x in ["pending", "approved", "out", "returned", "rejected", "cancelled"]], default="pending")
    handover_note = models.TextField(blank=True, max_length=1000)
    return_note = models.TextField(blank=True, max_length=1000)
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["start", "pk"]
        constraints = [models.CheckConstraint(condition=Q(end__gte=F("start")), name="valid_date_window")]
