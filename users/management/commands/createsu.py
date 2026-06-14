import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create superuser from environment variables (for Render deployment)'

    def handle(self, *args, **kwargs):
        email    = os.environ.get('DJANGO_SUPERUSER_EMAIL',    'admin@ems.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Admin@12345')
        name     = os.environ.get('DJANGO_SUPERUSER_NAME',     'Admin')

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(
                f'Superuser {email} already exists. Skipping.'
            ))
            return

        try:
            User.objects.create_superuser(
                email=email,
                password=password,
                full_name=name,
                employee_id='ADMIN001',
                role='admin',
            )
            self.stdout.write(self.style.SUCCESS(
                f'✅ Superuser created: {email}'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed: {e}'))