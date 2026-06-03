import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from wiki.models import Company, CustomUser

company, created = Company.objects.get_or_create(
    cnpj="12.345.678/0001-99",
    defaults={
        'name': 'TechCorp S.A.',
        'domain': 'techcorp.com.br'
    }
)
print(f"Empresa Fictícia: {company.name} | CNPJ: {company.cnpj} | Domínio: {company.domain}")

user, created = CustomUser.objects.get_or_create(
    username="superadmin",
    defaults={
        'email': 'admin@techcorp.com.br',
        'role': 'SUPERADMIN',
        'employee_code': 'SUP-ADMIN01',
        'company': company,
        'is_superuser': True,
        'is_staff': True
    }
)
if created:
    user.set_password('admin123')
    user.save()
print(f"Superadmin criado: {user.username} | Código: {user.employee_code} | Senha: admin123")
