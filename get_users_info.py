import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from wiki.models import CustomUser

users = CustomUser.objects.select_related('company').all().order_by('company__name', 'role')

result = []
for user in users:
    company_name = user.company.name if user.company else "Sem Empresa (Global)"
    result.append({
        "username": user.username,
        "email": user.email,
        "role": user.get_role_display(),
        "employee_code": user.employee_code or "N/A",
        "company": company_name
    })

print(json.dumps(result, ensure_ascii=False, indent=2))
