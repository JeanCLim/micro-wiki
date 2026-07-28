import os
import django
from django.db.models import Q

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from wiki.models import Article

articles = Article.objects.filter(
    Q(title__icontains='xml') | Q(content__icontains='xml') | Q(title__icontains='envio')
)

if not articles:
    print("Nenhum artigo encontrado com 'xml' ou 'envio'.")
else:
    for a in articles:
        company_name = a.company.name if a.company else "Sem Empresa (Global)"
        print(f"Artigo: '{a.title}' -> Empresa: {company_name}")
