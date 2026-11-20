from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from .models import Equipment, Reservation

ACTIVE = ["pending", "approved", "out"]
def fail(message):
    raise ValidationError(message)

def lock_equipment(pk):
    # An UPDATE obtains SQLite's writer lock before any read/check/write.
    # select_for_update alone would be a no-op on SQLite.
    Equipment.objects.filter(pk=pk).update(revision=F("revision") + 1)
    return Equipment.objects.get(pk=pk)

def conflict(equipment, start, end, exclude=None):
    return Reservation.objects.filter(equipment=equipment, status__in=ACTIVE, start__lte=end, end__gte=start).exclude(pk=exclude).exists()

@transaction.atomic
def request_kit(*, equipment_id, borrower, start, end, purpose):
    equipment = lock_equipment(equipment_id)
    if not equipment.active:
        fail("This item is unavailable for new requests.")
    if start < timezone.localdate() or end < start:
        fail("Choose a start date today or later and an end date on or after it.")
    purpose = purpose.strip()
    if not purpose or len(purpose) > 240:
        fail("Add a purpose of 1 to 240 characters.")
    if conflict(equipment, start, end):
        fail("Those dates overlap a pending, approved or checked-out reservation.")
    return Reservation.objects.create(equipment=equipment, borrower=borrower, start=start, end=end, purpose=purpose)

@transaction.atomic
def transition(*, reservation_id, actor, action, note=""):
    equipment_id = Reservation.objects.values_list("equipment_id", flat=True).get(pk=reservation_id)
    lock_equipment(equipment_id)
    r = Reservation.objects.select_related("equipment").get(pk=reservation_id)
    if len(note) > 1000:
        fail("Condition notes must be at most 1000 characters.")
    if action == "cancel":
        if actor.pk != r.borrower_id and not actor.is_staff:
            raise PermissionDenied
        if r.status not in ["pending", "approved"]:
            fail("Only pending or approved requests can be cancelled.")
        r.status = "cancelled"
    else:
        if not actor.is_staff:
            raise PermissionDenied
        expected = {"approve": "pending", "reject": "pending", "checkout": "approved", "return": "out"}
        if action not in expected or r.status != expected[action]:
            fail("This action does not match the reservation's current state.")
        if action == "approve":
            if r.start < timezone.localdate():
                fail("This request starts in the past. Cancel it and create a new one.")
            if not r.equipment.active or conflict(r.equipment, r.start, r.end, r.pk):
                fail("The item is unavailable or these dates now conflict.")
            r.status = "approved"
        elif action == "checkout":
            if not r.start <= timezone.localdate() <= r.end:
                fail("Checkout is allowed only inside the approved date window.")
            if Reservation.objects.filter(equipment=r.equipment, status="out").exclude(pk=r.pk).exists():
                fail("This item is still checked out. Record its return first.")
            r.status, r.handover_note = "out", note.strip()
        elif action == "return":
            r.status, r.return_note = "returned", note.strip()
        else:
            r.status = "rejected"
    r.save()
    return r
