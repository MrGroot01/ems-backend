#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py shell -c "
from users.models import User
print('=== ALL USERS IN RENDER DATABASE ===')
for u in User.objects.all():
    print(f'Email: {u.email} | Name: {u.full_name} | Active: {u.is_active}')
print('=== END ===')
"