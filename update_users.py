import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from wiki.models import CustomUser

# Filtrar usuários que não são COMMON, não são SUPERADMIN, e não são os superadmins de empresa (cujo código começa com SUPER-)
target_users = CustomUser.objects.filter(
    role__in=['EMPLOYEE', 'ADMIN']
).exclude(
    employee_code__startswith='SUPER-'
)

# Clear first to avoid unique constraints
for u in target_users:
    u.employee_code = None
    u.save()

counter = 1
for user in target_users:
    # O usuário pediu "codigo com nome e final 1, 2, 3..."
    # Como first_name está vazio, vamos usar a palavra literal "nome" + número, ou se tiver username usamos ele?
    # Para simplificar e seguir literalmente "nome1", "nome2", usaremos "nome" + contador.
    code = f"nome{counter}"
    user.employee_code = code
    user.set_password(code)
    user.save()
    print(f"Atualizado: {user.username} (Role: {user.role}) -> Código/Senha: {code}")
    counter += 1

print("Concluído!")
