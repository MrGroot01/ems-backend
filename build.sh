#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Show all users
python manage.py shell -c "
from users.models import User
print('=== ALL USERS ===')
for u in User.objects.all():
    print(f'Email: {u.email} | is_staff: {u.is_staff} | is_superuser: {u.is_superuser}')
print('=== END ===')
"

# Delete and recreate superuser cleanly
python manage.py shell -c "
import os
from users.models import User

email    = os.environ.get('DJANGO_SUPERUSER_EMAIL',    'admin@ems.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Admin@12345')
name     = os.environ.get('DJANGO_SUPERUSER_NAME',     'Admin')
emp_id   = os.environ.get('DJANGO_SUPERUSER_EMP_ID',   'ADMIN001')

if User.objects.filter(email=email).exists():
    User.objects.filter(email=email).delete()
    print(f'Deleted old: {email}')

if User.objects.filter(employee_id=emp_id).exists():
    emp_id = 'ADMIN-SUPER-01'

u = User(email=email, full_name=name, employee_id=emp_id, role='admin', is_staff=True, is_superuser=True, is_active=True)
u.set_password(password)
u.save()

check = User.objects.get(email=email)
print(f'Created: {check.email} | is_staff={check.is_staff} | password_ok={check.check_password(password)}')
"