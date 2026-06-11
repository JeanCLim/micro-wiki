from .models import Category, FavoriteArticle, Tag

def sidebar_context(request):
    """
    Fornece as categorias e seus artigos publicados para todas as páginas isolando por empresa.
    """
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return {'sidebar_categories': Category.objects.none(), 'sidebar_favorites': [], 'all_tags': []}

    user = request.user
    if getattr(user, 'company', None):
        categories = Category.objects.filter(company=user.company).prefetch_related('articles')
    else:
        categories = Category.objects.filter(company__isnull=True).prefetch_related('articles')

    sidebar_favorites = FavoriteArticle.objects.filter(user=user).select_related('article')
    all_tags = Tag.objects.all().order_by('name')

    return {
        'sidebar_categories': categories,
        'sidebar_favorites': sidebar_favorites,
        'all_tags': all_tags
    }
