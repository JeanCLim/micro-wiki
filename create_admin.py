import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from wiki.models import CustomUser, Company

company = Company.objects.first()

if not company:
    print("Nenhuma empresa encontrada.")
else:
    # Create an admin for this company
    username = f"admin_{company.id}"
    email = f"admin@{company.id}.com"
    
    user, created = CustomUser.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'role': 'ADMIN',
            'company': company,
            'employee_code': f'ADM-{company.id}'
        }
    )
    user.set_password('admin123')
    user.role = 'ADMIN' # ensure it's not superadmin
    user.save()
    
    print(f"Admin criado com sucesso!")
    print(f"Empresa: {company.name}")
    print(f"Email: {user.email}")
    print(f"Código Funcionário: {user.employee_code}")
    print(f"Senha: admin123")
