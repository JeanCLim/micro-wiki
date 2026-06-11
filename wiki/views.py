from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, View, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.db.models import Q
from .models import Article, Category
from .decorators import role_required

class GatewayView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, 'gateway.html')

    def post(self, request):
        company_code = request.POST.get('company_code', '').strip()
        import os
        master_code = os.environ.get('MASTER_CODE', 'master123')
        
        if company_code == master_code or company_code.lower() == 'master code':
            from .models import CustomUser
            if CustomUser.objects.filter(role='SUPERADMIN', company__isnull=True).exists():
                request.session['company_code'] = 'Acesso Master'
                request.session['is_master'] = True
                if 'company_id' in request.session:
                    del request.session['company_id']
                return redirect('login')
            else:
                return render(request, 'gateway.html', {'error': 'Nenhum Superadmin global configurado.'})
                
        if company_code:
            from .models import Company
            company = Company.objects.filter(Q(cnpj=company_code) | Q(domain=company_code)).first()
            if company:
                if not company.is_active:
                    return render(request, 'gateway.html', {'error': 'Acesso suspenso: Este Workspace encontra-se inativo.'})
                request.session['company_code'] = company.name
                request.session['company_id'] = company.id
                if 'is_master' in request.session:
                    del request.session['is_master']
                return redirect('login')
            else:
                return render(request, 'gateway.html', {'error': 'Empresa não encontrada. Verifique o CNPJ ou Domínio.'})
        return render(request, 'gateway.html', {'error': 'Insira o código ou domínio da empresa.'})

class CustomLoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        if not request.session.get('company_code'):
            return redirect('gateway')
            
        if request.session.get('is_master'):
            return render(request, 'master_login.html')
            
        return render(request, 'login.html')

    def post(self, request):
        login_type = request.POST.get('login_type')
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password, login_type=login_type)
        if user is not None:
            if request.session.get('is_master') and user.role != 'SUPERADMIN':
                return render(request, 'master_login.html', {'error': 'Esta conta não possui privilégios globais (Master).'})
            if not request.session.get('is_master') and user.role == 'SUPERADMIN':
                return render(request, 'login.html', {'error': 'Superadmins devem realizar login através do código Master no Gateway.'})
                
            login(request, user)
            if user.role == 'SUPERADMIN':
                request.session.set_expiry(0)
                return redirect('master_admin')
            return redirect('home')
        else:
            if request.session.get('is_master'):
                return render(request, 'master_login.html', {'error': 'Credenciais inválidas.'})
            return render(request, 'login.html', {'error': 'Credenciais inválidas.'})

class CustomLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')

class HomeView(LoginRequiredMixin, ListView):
    model = Article
    template_name = 'home.html'
    context_object_name = 'articles'
    
    def get_queryset(self):
        user = self.request.user
        qs = Article.objects.filter(status='APPROVED')
        if getattr(user, 'company', None):
            qs = qs.filter(category__company=user.company)
        else:
            qs = qs.filter(category__company__isnull=True)
        return qs.order_by('-created_at')[:10]
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        if company:
            context['sidebar_categories'] = Category.objects.filter(company=company)
            base_qs = Article.objects.filter(status='APPROVED', category__company=company)
        else:
            context['sidebar_categories'] = Category.objects.filter(company__isnull=True)
            base_qs = Article.objects.filter(status='APPROVED', category__company__isnull=True)
            
        from .models import FavoriteArticle
        fav_ids = FavoriteArticle.objects.filter(user=self.request.user).values('article')
        context['favorite_articles'] = base_qs.filter(id__in=fav_ids).order_by('-created_at')
        
        return context

class ArticleDetailView(LoginRequiredMixin, DetailView):
    model = Article
    template_name = 'article_detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        user = self.request.user
        qs = Article.objects.all()
        if getattr(user, 'company', None):
            qs = qs.filter(category__company=user.company)
        else:
            qs = qs.filter(category__company__isnull=True)
            
        if user.is_authenticated and user.role in ['ADMIN', 'SUPERADMIN']:
            return qs
        elif user.is_authenticated:
            return qs.filter(Q(status='APPROVED') | Q(author=user))
        return qs.filter(status='APPROVED')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_articles'] = Article.objects.filter(category=self.object.category, status='APPROVED').exclude(id=self.object.id)[:5]
        from .models import FavoriteArticle
        context['is_favorited'] = FavoriteArticle.objects.filter(user=self.request.user, article=self.object).exists() if self.request.user.is_authenticated else False
        return context

class CategoryDetailView(LoginRequiredMixin, ListView):
    model = Article
    template_name = 'category_detail.html'
    context_object_name = 'articles'
    
    def get_queryset(self):
        company = self.request.user.company
        if company:
            self.category = get_object_or_404(Category, slug=self.kwargs['slug'], company=company)
        else:
            self.category = get_object_or_404(Category, slug=self.kwargs['slug'], company__isnull=True)
        return Article.objects.filter(category=self.category, status='APPROVED')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        company = self.request.user.company
        if company:
            context['categories'] = Category.objects.filter(company=company)
        else:
            context['categories'] = Category.objects.filter(company__isnull=True)
        return context

class SearchView(LoginRequiredMixin, ListView):
    model = Article
    template_name = 'search_results.html'
    context_object_name = 'articles'

    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        tag_filter = self.request.GET.get('tag', '').strip()
        
        if query or tag_filter:
            user = self.request.user
            qs = Article.objects.filter(status='APPROVED')
            
            if query:
                qs = qs.filter(Q(title__icontains=query) | Q(content__icontains=query))
                
            if tag_filter:
                qs = qs.filter(tags__name=tag_filter)

            if getattr(user, 'company', None):
                qs = qs.filter(category__company=user.company)
            else:
                qs = qs.filter(category__company__isnull=True)
            return qs
        return Article.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['selected_tag'] = self.request.GET.get('tag', '')
        return context

def custom_404(request, exception):
    return render(request, 'em_desenvolvimento.html', status=404)

from django.http import JsonResponse
from django.utils.text import slugify
from .models import Article, Category, Tag, ApprovalNotification, SystemUpdate

@method_decorator(role_required('EMPLOYEE', 'ADMIN', 'SUPERADMIN'), name='dispatch')
class ArticleFrontendCreateView(LoginRequiredMixin, View):
    def get(self, request):
        company = request.user.company
        from .models import ArticleTemplate
        if company:
            categories = Category.objects.filter(company=company)
            templates = ArticleTemplate.objects.filter(company=company)
        else:
            categories = Category.objects.filter(company__isnull=True)
            templates = ArticleTemplate.objects.filter(company__isnull=True)
            
        context = {'categories': categories, 'templates': templates}
        
        template_id = request.GET.get('template_id')
        if template_id:
            context['initial_template'] = get_object_or_404(ArticleTemplate, id=template_id)
            
        return render(request, 'article_editor.html', context)

    def post(self, request):
        from .services import create_article
        from django.core.exceptions import ValidationError
        
        title = request.POST.get('title')
        content = request.POST.get('content')
        category_id = request.POST.get('category')
        tags_raw = request.POST.get('tags', '')
        visibility = request.POST.get('visibility', 'PUBLIC')
        action = request.POST.get('action') # 'draft' ou 'pending'
        cover_image = request.FILES.get('cover_image')
        attachment = request.FILES.get('attachment')
        
        version = request.POST.get('version', '01')
        valid_until = request.POST.get('valid_until', '')
        changes_summary = request.POST.get('changes_summary', 'Criação')
        responsible_area = request.POST.get('responsible_area', '')

        try:
            article = create_article(
                user=request.user,
                title=title,
                content=content,
                category_id=category_id,
                tags_raw=tags_raw,
                visibility=visibility,
                action=action,
                cover_image=cover_image,
                attachment=attachment,
                version=version,
                valid_until=valid_until,
                changes_summary=changes_summary,
                responsible_area=responsible_area
            )
            return JsonResponse({'success': True, 'url': article.get_absolute_url()})
        except ValidationError as e:
            return JsonResponse({'success': False, 'error': str(e.message) if hasattr(e, 'message') else str(e)}, status=400)

@method_decorator(role_required('ADMIN', 'SUPERADMIN'), name='dispatch')
class ArticleReviewView(LoginRequiredMixin, View):
    def post(self, request, slug):
        article = get_object_or_404(Article, slug=slug)
        action = request.POST.get('action')
        
        if action == 'approve':
            article.status = 'APPROVED'
            article.save()
            ApprovalNotification.objects.filter(article=article).update(is_read=True)
        elif action == 'reject':
            article.status = 'REJECTED'
            article.save()
            ApprovalNotification.objects.filter(article=article).update(is_read=True)
            
        return redirect('article_detail', slug=slug)

class ToggleDarkModeAPIView(LoginRequiredMixin, View):
    def post(self, request):
        user = request.user
        user.dark_mode = not user.dark_mode
        user.save()
        return JsonResponse({'success': True, 'dark_mode': user.dark_mode})

class NotificationsAPIView(LoginRequiredMixin, View):
    def get(self, request):
        data = {'approvals': [], 'systems': []}
        
        if request.user.role in ['ADMIN', 'SUPERADMIN']:
            approvals = ApprovalNotification.objects.filter(is_read=False).order_by('-created_at')
            data['approvals'] = [
                {
                    'id': a.id,
                    'title': a.article.title,
                    'author': a.article.author.username,
                    'url': a.article.get_absolute_url(),
                    'date': a.created_at.strftime("%d/%m/%Y %H:%M")
                } for a in approvals
            ]
            
        systems = SystemUpdate.objects.order_by('-created_at')[:5]
        data['systems'] = [
            {
                'id': s.id,
                'title': s.title,
                'message': s.message,
                'version': s.version,
                'date': s.created_at.strftime("%d/%m/%Y")
            } for s in systems
        ]
        
        return JsonResponse(data)

@method_decorator(role_required('ADMIN', 'SUPERADMIN'), name='dispatch')
class CategoryCreateAPIView(LoginRequiredMixin, View):
    def post(self, request):
        from .services import create_category
        from django.core.exceptions import ValidationError
        
        name = request.POST.get('name')
        is_special_raw = request.POST.get('is_special')
        
        try:
            category = create_category(user=request.user, name=name, is_special_raw=is_special_raw)
            return JsonResponse({'success': True, 'id': category.id, 'name': category.name})
        except ValidationError as e:
            return JsonResponse({'success': False, 'error': str(e.message) if hasattr(e, 'message') else str(e)}, status=400)

class UserProfileView(LoginRequiredMixin, View):
    def get(self, request):
        articles = Article.objects.filter(author=request.user).order_by('-updated_at')
        return render(request, 'profile.html', {'articles': articles})

@method_decorator(role_required('ADMIN', 'SUPERADMIN'), name='dispatch')
class SettingsView(LoginRequiredMixin, View):
    def get(self, request):
        from .models import WorkspaceSettings
        company = request.user.company
        settings_obj = None
        if company:
            # Exclude SUPERADMIN
            users_qs = company.users.exclude(role='SUPERADMIN')
            users = list(users_qs)
            for u in users:
                u.recent_articles = Article.objects.filter(author=u).order_by('-updated_at')[:3]
                
            categories = Category.objects.filter(company=company)
            from .models import ArticleTemplate
            article_templates = ArticleTemplate.objects.filter(company=company)
            settings_obj, _ = WorkspaceSettings.objects.get_or_create(company=company)
        else:
            users = []
            categories = []
            article_templates = []
        return render(request, 'settings.html', {'company': company, 'users': users, 'categories': categories, 'settings': settings_obj, 'article_templates': article_templates})
        
    def post(self, request):
        from .models import WorkspaceSettings, CustomUser
        action = request.POST.get('action')
        company = request.user.company
        
        if not company:
            return redirect('settings')
            
        if action == 'update_company':
            company.name = request.POST.get('name', company.name)
            company.domain = request.POST.get('domain', company.domain)
            company.save()
            
        elif action == 'update_branding':
            settings_obj, _ = WorkspaceSettings.objects.get_or_create(company=company)
            settings_obj.primary_color = request.POST.get('primary_color', settings_obj.primary_color)
            if 'favicon' in request.FILES:
                settings_obj.favicon = request.FILES['favicon']
            
            if request.POST.get('font_family'):
                settings_obj.font_family = request.POST.get('font_family')
                
            if request.POST.get('border_style'):
                settings_obj.border_style = request.POST.get('border_style')
                
            if request.POST.get('theme_preference'):
                settings_obj.theme_preference = request.POST.get('theme_preference')
                
            settings_obj.compact_layout = request.POST.get('compact_layout') == 'on'
            settings_obj.force_dark_mode = request.POST.get('force_dark_mode') == 'on'
            
            settings_obj.save()
            
        elif action == 'update_security':
            settings_obj, _ = WorkspaceSettings.objects.get_or_create(company=company)
            settings_obj.require_2fa = request.POST.get('require_2fa') == 'on'
            settings_obj.session_timeout_minutes = int(request.POST.get('session_timeout_minutes', settings_obj.session_timeout_minutes))
            settings_obj.save()
            
        elif action == 'delete_category':
            cat_id = request.POST.get('category_id')
            cat = Category.objects.filter(id=cat_id, company=company).first()
            if cat:
                if cat.is_special and request.user.role != 'ADMIN' and request.user.role != 'SUPERADMIN':
                    from django.http import HttpResponseForbidden
                    return HttpResponseForbidden('Acesso negado: Somente administradores podem excluir categorias especiais.')
                cat.delete()
            
        elif action == 'update_role':
            user_id = request.POST.get('user_id')
            new_role = request.POST.get('role')
            u = CustomUser.objects.filter(id=user_id, company=company).first()
            if u and u != request.user:
                u.role = new_role
                u.save()
                
        return redirect('settings')

@method_decorator(role_required('ADMIN', 'SUPERADMIN'), name='dispatch')
class UserCreateAPIView(LoginRequiredMixin, View):
    def post(self, request):
        from .models import CustomUser
        company = request.user.company
        if not company:
            return JsonResponse({'success': False, 'error': 'Você não tem uma empresa vinculada.'}, status=400)
            
        username = request.POST.get('username')
        email = request.POST.get('email', '')
        role = request.POST.get('role', 'COMMON')
        
        if CustomUser.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'error': 'Usuário já existe.'}, status=400)
            
        u = CustomUser.objects.create_user(username=username, email=email, password='changeme123', role=role, company=company)
        return JsonResponse({'success': True, 'id': u.id, 'username': u.username, 'role': u.get_role_display()})

@method_decorator(role_required('EMPLOYEE', 'ADMIN', 'SUPERADMIN'), name='dispatch')
class ArticleFrontendUpdateView(LoginRequiredMixin, View):
    def get(self, request, slug):
        article = get_object_or_404(Article, slug=slug)
        # Verify permissions: must be ADMIN or SUPERADMIN
        if request.user.role not in ['ADMIN', 'SUPERADMIN']:
            return redirect('home')
            
        company = request.user.company
        if company:
            categories = Category.objects.filter(company=company)
        else:
            categories = Category.objects.filter(company__isnull=True)
            
        return render(request, 'article_editor.html', {'categories': categories, 'article': article})

    def post(self, request, slug):
        from .services import update_article
        from django.core.exceptions import ValidationError
        
        article = get_object_or_404(Article, slug=slug)
        if request.user.role not in ['ADMIN', 'SUPERADMIN']:
            return JsonResponse({'success': False, 'error': 'Permissão negada. Apenas administradores podem editar artigos.'}, status=403)
            
        title = request.POST.get('title')
        content = request.POST.get('content')
        category_id = request.POST.get('category')
        tags_raw = request.POST.get('tags', '')
        visibility = request.POST.get('visibility', 'PUBLIC')
        action = request.POST.get('action')
        cover_image = request.FILES.get('cover_image')
        attachment = request.FILES.get('attachment')
        
        version = request.POST.get('version', '01')
        valid_until = request.POST.get('valid_until', '')
        changes_summary = request.POST.get('changes_summary', 'Criação')
        responsible_area = request.POST.get('responsible_area', '')
        
        try:
            article = update_article(
                article=article,
                user=request.user,
                title=title,
                content=content,
                category_id=category_id,
                tags_raw=tags_raw,
                visibility=visibility,
                action=action,
                cover_image=cover_image,
                attachment=attachment,
                version=version,
                valid_until=valid_until,
                changes_summary=changes_summary,
                responsible_area=responsible_area
            )
            return JsonResponse({'success': True, 'url': article.get_absolute_url()})
        except ValidationError as e:
            return JsonResponse({'success': False, 'error': str(e.message) if hasattr(e, 'message') else str(e)}, status=400)

from .decorators import global_superadmin_required

@method_decorator(global_superadmin_required(), name='dispatch')
class MasterAdminView(LoginRequiredMixin, View):
    def get(self, request):
        from .models import Company, CustomUser, Category
        companies = Company.objects.all()
        # Exclude self to not show the superadmin in the list
        users = CustomUser.objects.exclude(id=request.user.id)
        categories = Category.objects.filter(company__isnull=True)
        
        online_users = sum(1 for u in users if u.is_online)
        
        context = {
            'companies': companies,
            'users': users,
            'total_users': users.count(),
            'online_users': online_users,
            'categories': categories,
            'total_companies': companies.count()
        }
        return render(request, 'master_dashboard.html', context)
        
    def post(self, request):
        from .models import Company, CustomUser, Category
        action = request.POST.get('action')
        
        if action == 'create_company':
            name = request.POST.get('name')
            cnpj = request.POST.get('cnpj')
            domain = request.POST.get('domain')
            if name and cnpj:
                Company.objects.create(name=name, cnpj=cnpj, domain=domain)
        elif action == 'toggle_company':
            comp_id = request.POST.get('company_id')
            comp = Company.objects.filter(id=comp_id).first()
            if comp:
                comp.is_active = not comp.is_active
                comp.save()
        elif action == 'delete_user':
            user_id = request.POST.get('user_id')
            CustomUser.objects.filter(id=user_id).delete()
        elif action == 'inject_category':
            name = request.POST.get('name')
            target = request.POST.get('target') # 'all' or company_id
            if name:
                from django.utils.text import slugify
                slug = slugify(name)
                if target == 'all':
                    for comp in Company.objects.all():
                        if not Category.objects.filter(slug=slug, company=comp).exists():
                            Category.objects.create(name=name, slug=slug, company=comp, is_special=True)
                else:
                    comp = Company.objects.filter(id=target).first()
                    if comp and not Category.objects.filter(slug=slug, company=comp).exists():
                        Category.objects.create(name=name, slug=slug, company=comp, is_special=True)
        return redirect('master_admin')

class FavoriteToggleAPIView(LoginRequiredMixin, View):
    def post(self, request, slug):
        from .models import FavoriteArticle
        article = get_object_or_404(Article, slug=slug)
        fav, created = FavoriteArticle.objects.get_or_create(user=request.user, article=article)
        if not created:
            fav.delete()
            return JsonResponse({"favorited": False, "slug": slug})
        return JsonResponse({
            "favorited": True, 
            "slug": slug,
            "title": article.title,
            "url": article.get_absolute_url()
        })

class TemplateDataAPIView(LoginRequiredMixin, View):
    def get(self, request, template_id):
        from .models import ArticleTemplate
        from django.http import JsonResponse
        t = get_object_or_404(ArticleTemplate, id=template_id)
        
        # Verify if template belongs to the same company
        if t.company and request.user.company and t.company != request.user.company:
            return JsonResponse({'error': 'Acesso negado'}, status=403)
            
        return JsonResponse({
            'title': t.title,
            'content_html': t.content_html,
            'category_id': t.category.id if t.category else '',
            'default_tags': t.default_tags,
            'default_visibility': t.default_visibility
        })
