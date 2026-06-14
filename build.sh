#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Show all users in Render database
python manage.py shell -c "
from users.models import User
print('=== ALL USERS IN RENDER DATABASE ===')
for u in User.objects.all():
    print(f'Email: {u.email} | Name: {u.full_name} | Role: {u.role} | Active: {u.is_active}')
print(f'Total: {User.objects.count()} users')
print('=== END ===')
"

# Auto-create superuser if not exists
python manage.py shell -c "
import os
from users.models import User

email    = os.environ.get('DJANGO_SUPERUSER_EMAIL',    'admin@ems.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Admin@12345')
name     = os.environ.get('DJANGO_SUPERUSER_NAME',     'Admin')
emp_id   = os.environ.get('DJANGO_SUPERUSER_EMP_ID',   'ADMIN001')

# Check by email (safe — won't duplicate)
if User.objects.filter(email=email).exists():
    print(f'✅ Superuser already exists: {email} — skipping.')
else:
    # Make sure employee_id is also unique
    if User.objects.filter(employee_id=emp_id).exists():
        emp_id = 'ADMIN-SUPER'

    User.objects.create_superuser(
        email=email,
        password=password,
        full_name=name,
        employee_id=emp_id,
        role='admin',
    )
    print(f'✅ Superuser created: {email} (emp_id={emp_id})')
"