from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import OperationalError
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Equipment, Reservation
from .forms import RequestForm, EquipmentForm
from .services import request_kit, transition

@login_required
def home(request):
    form = RequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        try:
            request_kit(equipment_id=d["equipment"].pk, borrower=request.user, start=d["start"], end=d["end"], purpose=d["purpose"])
        except ValidationError as exc:
            form.add_error(None, exc)
        except OperationalError:
            form.add_error(None, "The database is busy. Nothing was reserved. Try again.")
        else:
            messages.success(request, "Request saved. Its dates are held while an admin reviews it.")
            return redirect("home")
    all_reservations = Reservation.objects.select_related("equipment", "borrower")
    mine = all_reservations if request.user.is_staff else all_reservations.filter(borrower=request.user)
    return render(request, "home.html", {"form": form, "equipment": Equipment.objects.all(), "reservations": mine, "schedule": all_reservations.filter(status__in=["pending", "approved", "out"]), "today": timezone.localdate(), "pending_count": all_reservations.filter(status="pending").count(), "out_count": all_reservations.filter(status="out").count(), "due_count": all_reservations.filter(status="out", end__lte=timezone.localdate()).count()})

@login_required
@require_POST
def action(request, pk):
    get_object_or_404(Reservation, pk=pk)
    try:
        transition(reservation_id=pk, actor=request.user, action=request.POST.get("action"), note=request.POST.get("note", ""))
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
    except OperationalError:
        messages.error(request, "The database is busy. No change was saved. Try again.")
    else:
        messages.success(request, "Reservation updated.")
    return redirect("home")

@login_required
@user_passes_test(lambda u: u.is_staff)
def equipment(request):
    form = EquipmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Equipment added.")
        return redirect("home")
    return render(request, "equipment.html", {"form": form})
