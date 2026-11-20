from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import IntegrityError, transaction
from django.utils import timezone
from .models import Equipment, Reservation
from .services import request_kit, transition

class ReservationTests(TestCase):
    def setUp(self):
        self.member = get_user_model().objects.create_user("member")
        self.other = get_user_model().objects.create_user("other")
        self.admin = get_user_model().objects.create_user("admin", is_staff=True)
        self.kit = Equipment.objects.create(name="Camera")
        self.today = timezone.localdate()
    def reserve(self, **kw):
        d = dict(equipment_id=self.kit.pk, borrower=self.member, start=self.today, end=self.today+timedelta(days=2), purpose="Workshop")
        d.update(kw)
        return request_kit(**d)
    def move(self, r, action, actor=None, note=""):
        return transition(reservation_id=r.pk, actor=actor or self.admin, action=action, note=note)
    def test_new_request_pending(self):
        self.assertEqual(self.reserve().status, "pending")
    def test_exact_overlap(self):
        self.reserve()
        with self.assertRaises(ValidationError): self.reserve()
    def test_shared_return_day_conflicts(self):
        self.reserve()
        with self.assertRaises(ValidationError): self.reserve(start=self.today+timedelta(days=2),end=self.today+timedelta(days=3))
    def test_next_day_allowed(self):
        self.reserve()
        self.assertEqual(self.reserve(start=self.today+timedelta(days=3),end=self.today+timedelta(days=4)).status,"pending")
    def test_containing_overlap(self):
        self.reserve(start=self.today+timedelta(days=1))
        with self.assertRaises(ValidationError): self.reserve(end=self.today+timedelta(days=3))
    def test_other_equipment_allowed(self):
        self.reserve()
        kit=Equipment.objects.create(name="Tripod")
        self.reserve(equipment_id=kit.pk)
    def test_past_rejected(self):
        with self.assertRaises(ValidationError): self.reserve(start=self.today-timedelta(days=1))
    def test_reversed_rejected(self):
        with self.assertRaises(ValidationError): self.reserve(end=self.today-timedelta(days=1))
    def test_empty_purpose(self):
        with self.assertRaises(ValidationError): self.reserve(purpose=" ")
    def test_inactive_equipment(self):
        self.kit.active=False; self.kit.save()
        with self.assertRaises(ValidationError): self.reserve()
    def test_full_lifecycle_and_notes(self):
        r=self.reserve()
        self.move(r,"approve")
        self.move(r,"checkout",note="One battery")
        r=self.move(r,"return",note="All present")
        self.assertEqual((r.status,r.handover_note,r.return_note),("returned","One battery","All present"))
    def test_member_cannot_approve(self):
        with self.assertRaises(PermissionDenied): self.move(self.reserve(),"approve",self.member)
    def test_other_member_cannot_cancel(self):
        with self.assertRaises(PermissionDenied): self.move(self.reserve(),"cancel",self.other)
    def test_owner_cancel_releases_dates(self):
        self.move(self.reserve(),"cancel",self.member)
        self.reserve()
    def test_decline_releases_dates(self):
        self.move(self.reserve(),"reject")
        self.reserve()
    def test_no_return_before_checkout(self):
        with self.assertRaises(ValidationError): self.move(self.reserve(),"return")
    def test_out_cannot_cancel(self):
        r=self.reserve();self.move(r,"approve");self.move(r,"checkout")
        with self.assertRaises(ValidationError):self.move(r,"cancel",self.member)
    def test_note_length(self):
        with self.assertRaises(ValidationError):self.move(self.reserve(),"approve",note="x"*1001)
    def test_future_checkout_rejected(self):
        r=self.reserve(start=self.today+timedelta(days=1)); self.move(r,"approve")
        with self.assertRaises(ValidationError):self.move(r,"checkout")
    def test_overdue_out_blocks_next_checkout(self):
        r=self.reserve();self.move(r,"approve");self.move(r,"checkout")
        Reservation.objects.filter(pk=r.pk).update(start=self.today-timedelta(days=3),end=self.today-timedelta(days=1))
        n=self.reserve();self.move(n,"approve")
        with self.assertRaises(ValidationError):self.move(n,"checkout")
    def test_login_required(self):
        self.assertEqual(self.client.get("/").status_code,302)
    def test_get_action_is_not_mutating(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(f"/reservation/{self.reserve().pk}/action/").status_code,405)
    def test_members_do_not_see_other_purpose_or_borrower(self):
        self.reserve(purpose="Private workshop notes")
        self.client.force_login(self.other)
        response=self.client.get("/")
        self.assertNotContains(response,"Private workshop notes")
        self.assertContains(response,"Camera")
    def test_csrf_required(self):
        c=Client(enforce_csrf_checks=True); c.force_login(self.member)
        self.assertEqual(c.post("/",{}).status_code,403)
    def test_script_purpose_escaped(self):
        self.reserve(purpose="<script>alert(1)</script>")
        self.client.force_login(self.member)
        self.assertContains(self.client.get("/"),"&lt;script&gt;")
    def test_member_no_add_equipment(self):
        self.client.force_login(self.member)
        self.client.post("/equipment/new/",{"name":"Not allowed"})
        self.assertFalse(Equipment.objects.filter(name="Not allowed").exists())
    def test_admin_add_equipment(self):
        self.client.force_login(self.admin)
        self.client.post("/equipment/new/",{"name":"Tripod","category":"Video","description":""})
        self.assertTrue(Equipment.objects.filter(name="Tripod").exists())
    def test_same_day_request_allowed(self):
        self.assertEqual(self.reserve(end=self.today).start,self.today)
    def test_pending_and_approved_both_hold_dates(self):
        r=self.reserve();self.move(r,"approve")
        with self.assertRaises(ValidationError):self.reserve()
    def test_model_constraint(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Reservation.objects.create(equipment=self.kit,borrower=self.member,start=self.today,end=self.today-timedelta(days=1),purpose="Bad")
