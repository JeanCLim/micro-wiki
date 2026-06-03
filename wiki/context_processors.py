from .models import Category

def sidebar_context(request):
    """
    Fornece as categorias e seus artigos publicados para todas as páginas isolando por empresa.
    """
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return {'sidebar_categories': Category.objects.none()}

    user = request.user
    if getattr(user, 'company', None):
        categories = Category.objects.filter(company=user.company).prefetch_related('articles')
    else:
        categories = Category.objects.filter(company__isnull=True).prefetch_related('articles')

    return {
        'sidebar_categories': categories
    }
