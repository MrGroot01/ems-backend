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
    print(f'Email: {u.email} | Name: {u.full_name} | Role: {u.role} | is_staff: {u.is_staff} | is_superuser: {u.is_superuser} | Active: {u.is_active}')
print(f'Total: {User.objects.count()} users')
print('=== END ===')
"

# Force create OR fix superuser
python manage.py shell -c "
import os
from users.models import User

email    = os.environ.get('DJANGO_SUPERUSER_EMAIL',    'admin@ems.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Admin@12345')
name     = os.environ.get('DJANGO_SUPERUSER_NAME',     'Admin')
emp_id   = os.environ.get('DJANGO_SUPERUSER_EMP_ID',   'ADMIN001')

if User.objects.filter(email=email).exists():
    # User exists — FORCE set staff/superuser flags and reset password
    u = User.objects.get(email=email)
    u.is_staff     = True
    u.is_superuser = True
    u.is_active    = True
    u.role         = 'admin'
    u.set_password(password)
    u.save()
    print(f'✅ Superuser FIXED: {email} | is_staff={u.is_staff} | is_superuser={u.is_superuser}')
else:
    # Make sure employee_id is unique
    if User.objects.filter(employee_id=emp_id).exists():
        emp_id = 'ADMIN-SUPER'

    u = User.objects.create_superuser(
        email=email,
        password=password,
        full_name=name,
        employee_id=emp_id,
        role='admin',
    )
    u.is_staff     = True
    u.is_superuser = True
    u.is_active    = True
    u.save()
    print(f'✅ Superuser CREATED: {email} | is_staff={u.is_staff} | is_superuser={u.is_superuser}')
"