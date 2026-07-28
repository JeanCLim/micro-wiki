import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from wiki.models import CustomUser

print("Users:")
for u in CustomUser.objects.all():
    print(f'{u.id} - {u.username} - {u.first_name} - {u.role} - {u.employee_code}')
