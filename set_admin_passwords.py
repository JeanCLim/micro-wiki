import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from wiki.models import CustomUser

# Reset passwords for known admins
admins = CustomUser.objects.filter(username__in=['superadmin', 'superadmin_company_4'])

for admin in admins:
    admin.set_password('admin123')
    admin.save()
    print(f"Password reset for {admin.username} to 'admin123'")

print("Done.")
