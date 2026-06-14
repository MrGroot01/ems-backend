#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input

# Make any missing migrations first
python manage.py makemigrations --no-input
python manage.py migrate

# Show all users
python manage.py shell -c "
from users.models import User
print('=== ALL USERS ===')
for u in User.objects.all():
    print(f'Email: {u.email} | is_staff: {u.is_staff} | is_superuser: {u.is_superuser}')
print('=== END ===')
"

# Fix superuser — only update flags, don't delete (avoids cascade errors)
python manage.py shell -c "
import os
from users.models import User

email    = os.environ.get('DJANGO_SUPERUSER_EMAIL',    'admin@ems.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Admin@12345')
emp_id   = os.environ.get('DJANGO_SUPERUSER_EMP_ID',   'ADMIN001')
name     = os.environ.get('DJANGO_SUPERUSER_NAME',     'Admin')

if User.objects.filter(email=email).exists():
    u = User.objects.get(email=email)
    u.is_staff     = True
    u.is_superuser = True
    u.is_active    = True
    u.role         = 'admin'
    u.set_password(password)
    u.save(update_fields=['is_staff','is_superuser','is_active','role','password'])
    print(f'FIXED: {u.email} | is_staff={u.is_staff} | is_superuser={u.is_superuser} | password_ok={u.check_password(password)}')
else:
    # Handle employee_id collision
    if User.objects.filter(employee_id=emp_id).exists():
        emp_id = 'ADMIN-SU-01'
    u = User(email=email, full_name=name, employee_id=emp_id, role='admin',
             is_staff=True, is_superuser=True, is_active=True)
    u.set_password(password)
    u.save()
    print(f'CREATED: {u.email} | password_ok={u.check_password(password)}')
"