from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os


class Command(BaseCommand):
    help = 'Create a development superuser from env vars or defaults (for local use only)'

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.getenv('DEV_SUPERUSER_USERNAME', 'admin')
        email = os.getenv('DEV_SUPERUSER_EMAIL', 'admin@example.com')
        password = os.getenv('DEV_SUPERUSER_PASSWORD', 'adminpass')

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'Superuser "{username}" already exists'))
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f'Created superuser "{username}"'))

