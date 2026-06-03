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
        else:
            context['sidebar_categories'] = Category.objects.filter(company__isnull=True)
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
        query = self.request.GET.get('q')
        if query:
            user = self.request.user
            qs = Article.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query),
                status='APPROVED'
            )
            if getattr(user, 'company', None):
                qs = qs.filter(category__company=user.company)
            else:
                qs = qs.filter(category__company__isnull=True)
            return qs
        return Article.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
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
        if company:
            categories = Category.objects.filter(company=company)
        else:
            categories = Category.objects.filter(company__isnull=True)
        return render(request, 'article_editor.html', {'categories': categories})

    def post(self, request):
        title = request.POST.get('title')
        content = request.POST.get('content')
        category_id = request.POST.get('category')
        tags_raw = request.POST.get('tags', '')
        action = request.POST.get('action') # 'draft' ou 'pending'

        if not title or not content or not category_id:
            return JsonResponse({'success': False, 'error': 'Campos obrigatórios faltando.'}, status=400)

        slug = slugify(title)
        category = get_object_or_404(Category, id=category_id)
        
        status = 'DRAFT'
        if action == 'pending':
            status = 'PENDING'
        if request.user.role in ['ADMIN', 'SUPERADMIN'] and action == 'publish':
            status = 'APPROVED'

        article = Article.objects.create(
            title=title,
            slug=slug,
            content=content,
            category=category,
            author=request.user,
            status=status
        )

        if tags_raw:
            tag_names = [t.strip() for t in tags_raw.split(',') if t.strip()]
            for t_name in tag_names:
                t_slug = slugify(t_name)
                tag_obj, _ = Tag.objects.get_or_create(slug=t_slug, defaults={'name': t_name})
                article.tags.add(tag_obj)
        
        if status == 'PENDING':
            ApprovalNotification.objects.create(article=article)

        return JsonResponse({'success': True, 'url': article.get_absolute_url()})

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
        name = request.POST.get('name')
        is_special_raw = request.POST.get('is_special')
        is_special = is_special_raw == 'on' or is_special_raw == 'true' or is_special_raw == '1'
        
        if not name:
            return JsonResponse({'success': False, 'error': 'Nome não informado.'}, status=400)
            
        slug = slugify(name)
        company = request.user.company
        
        # Verify if exists
        if Category.objects.filter(slug=slug, company=company).exists():
            return JsonResponse({'success': False, 'error': 'Categoria já existe.'}, status=400)
            
        category = Category.objects.create(
            name=name,
            slug=slug,
            company=company,
            is_special=is_special
        )
        
        return JsonResponse({'success': True, 'id': category.id, 'name': category.name})

class UserProfileView(LoginRequiredMixin, View):
    def get(self, request):
        articles = Article.objects.filter(author=request.user).order_by('-updated_at')
        return render(request, 'profile.html', {'articles': articles})

@method_decorator(role_required('ADMIN', 'SUPERADMIN'), name='dispatch')
class SettingsView(LoginRequiredMixin, View):
    def get(self, request):
        company = request.user.company
        if company:
            # Exclude SUPERADMIN
            users_qs = company.users.exclude(role='SUPERADMIN')
            users = list(users_qs)
            for u in users:
                u.recent_articles = Article.objects.filter(author=u).order_by('-updated_at')[:3]
                
            categories = Category.objects.filter(company=company)
        else:
            users = []
            categories = []
        return render(request, 'settings.html', {'company': company, 'users': users, 'categories': categories})
        
    def post(self, request):
        # Update Company Name
        action = request.POST.get('action')
        company = request.user.company
        
        if action == 'update_company' and company:
            company.name = request.POST.get('name', company.name)
            company.domain = request.POST.get('domain', company.domain)
            company.save()
            return redirect('settings')
            
        elif action == 'delete_category' and company:
            cat_id = request.POST.get('category_id')
            cat = Category.objects.filter(id=cat_id, company=company).first()
            if cat:
                if cat.is_special and request.user.role != 'ADMIN' and request.user.role != 'SUPERADMIN':
                    from django.http import HttpResponseForbidden
                    return HttpResponseForbidden('Acesso negado: Somente administradores podem excluir categorias especiais.')
                cat.delete()
            return redirect('settings')
            
        elif action == 'update_role' and company:
            user_id = request.POST.get('user_id')
            new_role = request.POST.get('role')
            from .models import CustomUser
            u = CustomUser.objects.filter(id=user_id, company=company).first()
            if u and u != request.user:
                u.role = new_role
                u.save()
            return redirect('settings')
            
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
        # Verify permissions: must be author or admin
        if article.author != request.user and request.user.role not in ['ADMIN', 'SUPERADMIN']:
            return redirect('home')
            
        company = request.user.company
        if company:
            categories = Category.objects.filter(company=company)
        else:
            categories = Category.objects.filter(company__isnull=True)
            
        return render(request, 'article_editor.html', {'categories': categories, 'article': article})

    def post(self, request, slug):
        article = get_object_or_404(Article, slug=slug)
        if article.author != request.user and request.user.role not in ['ADMIN', 'SUPERADMIN']:
            return JsonResponse({'success': False, 'error': 'Permissão negada.'}, status=403)
            
        title = request.POST.get('title')
        content = request.POST.get('content')
        category_id = request.POST.get('category')
        tags_raw = request.POST.get('tags', '')
        action = request.POST.get('action')
        
        if not title or not content or not category_id:
            return JsonResponse({'success': False, 'error': 'Campos obrigatórios faltando.'}, status=400)
            
        article.title = title
        article.slug = slugify(title)
        article.content = content
        article.category_id = category_id
        
        status = 'DRAFT'
        if action == 'pending':
            status = 'PENDING'
        if request.user.role in ['ADMIN', 'SUPERADMIN'] and action == 'publish':
            status = 'APPROVED'
            
        article.status = status
        article.save()
        
        # update tags
        article.tags.clear()
        if tags_raw:
            tag_names = [t.strip() for t in tags_raw.split(',') if t.strip()]
            for t_name in tag_names:
                t_slug = slugify(t_name)
                tag_obj, _ = Tag.objects.get_or_create(slug=t_slug, defaults={'name': t_name})
                article.tags.add(tag_obj)
                
        if status == 'PENDING':
            ApprovalNotification.objects.create(article=article)
            
        return JsonResponse({'success': True, 'url': article.get_absolute_url()})

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
