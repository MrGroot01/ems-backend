#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# DEBUG: Show all users with full flags
python manage.py shell -c "
from users.models import User
print('=== ALL USERS IN RENDER DATABASE ===')
for u in User.objects.all():
    print(f'Email: {u.email} | is_staff: {u.is_staff} | is_superuser: {u.is_superuser} | is_active: {u.is_active} | has_password: {bool(u.password)}')
print('=== END ===')
"

# Force fix superuser — delete and recreate cleanly
python manage.py shell -c "
import os
from users.models import User

email    = os.environ.get('DJANGO_SUPERUSER_EMAIL',    'admin@ems.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Admin@12345')
name     = os.environ.get('DJANGO_SUPERUSER_NAME',     'Admin')
emp_id   = os.environ.get('DJANGO_SUPERUSER_EMP_ID',   'ADMIN001')

# Delete old broken superuser if exists
if User.objects.filter(email=email).exists():
    User.objects.filter(email=email).delete()
    print(f'🗑️  Deleted old superuser: {email}')

# Handle employee_id collision
if User.objects.filter(employee_id=emp_id).exists():
    emp_id = 'ADMIN-SUPER-01'

# Create fresh
u = User(
    email=email,
    full_name=name,
    employee_id=emp_id,
    role='admin',
    is_staff=True,
    is_superuser=True,
    is_active=True,
)
u.set_password(password)   # hashes the password properly
u.save()

# Verify
check = User.objects.get(email=email)
print(f'✅ Superuser created fresh: {check.email}')
print(f'   is_staff={check.is_staff} | is_superuser={check.is_superuser} | is_active={check.is_active}')
print(f'   password_check={check.check_password(password)}')
"