from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone
from board.models import Equipment, Reservation
class Command(BaseCommand):
    help = "Add fictional local demo data. Passwords are NOT set; use changepassword."
    def handle(self, *args, **options):
        User = get_user_model()
        if User.objects.filter(username__in=["demo-admin", "demo-member"]).exists():
            raise CommandError("Demo users already exist. Refusing to modify their records.")
        admin = User.objects.create_user("demo-admin", is_staff=True)
        member = User.objects.create_user("demo-member")
        camera, _ = Equipment.objects.get_or_create(name="Demo camera 01", defaults={"category": "Video", "description": "Fictional mirrorless kit with a spare battery and strap."})
        Equipment.objects.get_or_create(name="Demo projector 01", defaults={"category": "Events", "description": "Fictional meeting-room projector with HDMI cable."})
        Equipment.objects.get_or_create(name="Demo audio kit 01", defaults={"category": "Sound", "description": "Fictional recorder and two clip-on microphones."})
        today = timezone.localdate()
        Reservation.objects.create(equipment=camera, borrower=member, start=today, end=today+timedelta(days=2), purpose="Fictional workshop recording", status="pending")
        self.stdout.write("Fictional demo created. No usable passwords were assigned. Run changepassword for demo-admin and demo-member.")
