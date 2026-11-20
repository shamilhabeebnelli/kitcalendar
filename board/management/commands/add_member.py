from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
class Command(BaseCommand):
    help = "Create a member with no usable password; then run changepassword."
    def add_arguments(self, parser):
        parser.add_argument("username")
    def handle(self, username, **options):
        if not username or len(username) > 150 or not all(c.isalnum() or c in "@.+-_" for c in username):
            raise CommandError("Use a valid username of 1 to 150 characters.")
        if get_user_model().objects.filter(username=username).exists():
            raise CommandError("That username already exists.")
        get_user_model().objects.create_user(username=username)
        self.stdout.write("Member created without a password. Now run changepassword for this username.")
