from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from .models import Company, Category

@receiver(post_save, sender=Company)
def create_default_categories(sender, instance, created, **kwargs):
    if created:
        default_categories = [
            "Suporte Técnico",
            "Procedimentos Internos",
            "Integrações"
        ]
        for name in default_categories:
            Category.objects.create(
                name=name,
                slug=slugify(name),
                company=instance
            )
            
        # Cria funcionário admin padrão da empresa
        from .models import CustomUser
        CustomUser.objects.create_user(
            username=f"superadmin_company_{instance.id}",
            password="admin123",
            role="ADMIN", # Todas as permissões a nível de empresa
            company=instance,
            first_name="Superadmin",
            last_name="Local",
            email=f"superadmin@{instance.cnpj}.com",
            employee_code=f"SUPER-{instance.id}"
        )
