from django.urls import path
from .views import (
    HomeView, ArticleDetailView, CategoryDetailView, SearchView, 
    CustomLoginView, CustomLogoutView, GatewayView,
    ArticleFrontendCreateView, ArticleReviewView, NotificationsAPIView,
    CategoryCreateAPIView, UserProfileView, SettingsView, UserCreateAPIView, ArticleFrontendUpdateView,
    MasterAdminView, FavoriteToggleAPIView, ToggleDarkModeAPIView, TemplateDataAPIView
)

urlpatterns = [
    path('acesso/', GatewayView.as_view(), name='gateway'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('master-admin/', MasterAdminView.as_view(), name='master_admin'),
    path('perfil/', UserProfileView.as_view(), name='profile'),
    path('configuracoes/', SettingsView.as_view(), name='settings'),
    path('artigos/novo/', ArticleFrontendCreateView.as_view(), name='article_create'),
    path('artigo/<slug:slug>/editar/', ArticleFrontendUpdateView.as_view(), name='article_update'),
    path('artigo/<slug:slug>/revisar/', ArticleReviewView.as_view(), name='article_review'),
    path('artigo/<slug:slug>/favoritar/', FavoriteToggleAPIView.as_view(), name='api_favorite_toggle'),
    path('api/notifications/', NotificationsAPIView.as_view(), name='api_notifications'),
    path('api/categories/novo/', CategoryCreateAPIView.as_view(), name='api_category_create'),
    path('api/users/novo/', UserCreateAPIView.as_view(), name='api_user_create'),
    path('api/toggle-dark-mode/', ToggleDarkModeAPIView.as_view(), name='api_toggle_dark_mode'),
    path('api/templates/<int:template_id>/', TemplateDataAPIView.as_view(), name='api_template_data'),
    path('', HomeView.as_view(), name='home'),
    path('search/', SearchView.as_view(), name='search'),
    path('category/<slug:slug>/', CategoryDetailView.as_view(), name='category_detail'),
    path('artigo/<slug:slug>/', ArticleDetailView.as_view(), name='article_detail'),
]
