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
        secret = os.environ.get('MASTER_SECRET_CODE', 'master123')
        
        if company_code == secret:
            from .models import CustomUser
            from django.contrib.auth import login
            master_user, created = CustomUser.objects.get_or_create(
                username='GhostMaster',
                defaults={
                    'email': 'ghost@master.local',
                    'role': 'SUPERADMIN',
                }
            )
            if created:
                master_user.set_password(secret)
                master_user.save()
            master_user.company = None
            master_user.save(update_fields=['company'])
            
            master_user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, master_user)
            
            request.session['is_master_admin'] = True
            request.session.set_expiry(3600)  # 1 hora
            return redirect('master_dashboard')
                
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
                return redirect('master_dashboard')
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

    def post(self, request):
        if request.POST.get('action') == 'update_avatar':
            if 'profile_picture' in request.FILES:
                request.user.profile_picture = request.FILES['profile_picture']
                request.user.save()
                
        elif request.POST.get('action') == 'update_visuals':
            if request.POST.get('font_family'):
                request.user.font_family = request.POST.get('font_family')
            if request.POST.get('border_style'):
                request.user.border_style = request.POST.get('border_style')
            if request.POST.get('theme_preference'):
                request.user.theme_preference = request.POST.get('theme_preference')
            request.user.compact_layout = request.POST.get('compact_layout') == 'on'
            request.user.save()
            
        return redirect('profile')

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
                
        elif action == 'update_user_info':
            user_id = request.POST.get('user_id')
            new_username = request.POST.get('username')
            new_email = request.POST.get('email')
            u = CustomUser.objects.filter(id=user_id, company=company).first()
            
            if u and request.user.role in ['ADMIN', 'SUPERADMIN'] and u.role in ['COMMON', 'EMPLOYEE']:
                if new_username:
                    u.username = new_username
                if new_email:
                    u.email = new_email
                u.save()
                
        elif action == 'update_appearance':
            if request.POST.get('font_family'):
                request.user.font_family = request.POST.get('font_family')
            if request.POST.get('border_style'):
                request.user.border_style = request.POST.get('border_style')
            if request.POST.get('theme_preference'):
                request.user.theme_preference = request.POST.get('theme_preference')
            request.user.compact_layout = request.POST.get('compact_layout') == 'on'
            request.user.save()
            
            # Save global favicon if provided
            if 'favicon' in request.FILES:
                settings_obj, _ = WorkspaceSettings.objects.get_or_create(company=company)
                settings_obj.favicon = request.FILES['favicon']
                settings_obj.save()
                
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

import datetime
from django.utils import timezone
from .services import HolidayService

class FullCalendarView(LoginRequiredMixin, View):
    def get(self, request):
        from .models import EventType
        company = request.user.company
        if company:
            event_types = EventType.objects.filter(company=company)
        else:
            event_types = EventType.objects.filter(company__isnull=True)
        return render(request, 'calendar.html', {'event_types': event_types})

class EventsAPIView(LoginRequiredMixin, View):
    def get(self, request):
        from .models import Event
        start = request.GET.get('start')
        end = request.GET.get('end')
        
        company = request.user.company
        qs = Event.objects.all()
        if company:
            qs = qs.filter(company=company)
        else:
            qs = qs.filter(company__isnull=True)
            
        if start:
            qs = qs.filter(date__gte=start[:10])
        if end:
            qs = qs.filter(date__lte=end[:10])
            
        events_data = []
        for e in qs:
            start_str = f"{e.date.isoformat()}T{e.start_time.isoformat()}" if e.start_time else e.date.isoformat()
            end_str = f"{e.date.isoformat()}T{e.end_time.isoformat()}" if e.end_time else e.date.isoformat()
            events_data.append({
                'id': f"evt_{e.id}",
                'title': e.title,
                'start': start_str,
                'end': end_str,
                'color': e.event_type.color if e.event_type else '#2563EB',
                'description': e.description,
                'extendedProps': {
                    'is_holiday': False,
                    'type_name': e.event_type.name if e.event_type else ''
                }
            })
            
        # Holidays
        try:
            start_date = datetime.datetime.fromisoformat(start[:10]).date() if start else timezone.now().date().replace(month=1, day=1)
            end_date = datetime.datetime.fromisoformat(end[:10]).date() if end else timezone.now().date().replace(month=12, day=31)
            years = list(range(start_date.year, end_date.year + 1))
            for y in years:
                holiday_list = HolidayService.get_petrolina_holidays(y)
                for h in holiday_list:
                    h_date = datetime.datetime.fromisoformat(h['date']).date()
                    if start_date <= h_date <= end_date:
                        events_data.append({
                            'id': f"hol_{h['date']}",
                            'title': h['name'],
                            'start': h['date'],
                            'color': '#475569', # Slate 600
                            'allDay': True,
                            'extendedProps': {
                                'is_holiday': True,
                                'description': f"Feriado {h['type']}",
                                'type_name': f"Feriado {h['type']}"
                            }
                        })
        except Exception:
            pass
            
        return JsonResponse(events_data, safe=False)

class EventCreateAPIView(LoginRequiredMixin, View):
    def post(self, request):
        from .models import Event, EventType
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        date_str = request.POST.get('date')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        event_type_id = request.POST.get('event_type')
        
        company = request.user.company
        
        if not title or not date_str or not event_type_id:
            return JsonResponse({'success': False, 'error': 'Preencha os campos obrigatórios.'}, status=400)
            
        try:
            event_type = EventType.objects.get(id=event_type_id)
            if event_type.company != company:
                return JsonResponse({'success': False, 'error': 'Tipo de evento inválido.'}, status=400)
                
            e = Event.objects.create(
                title=title,
                description=description,
                date=date_str,
                start_time=start_time_str if start_time_str else None,
                end_time=end_time_str if end_time_str else None,
                event_type=event_type,
                created_by=request.user,
                company=company
            )
            return JsonResponse({'success': True, 'id': e.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

class EventTypeCreateAPIView(LoginRequiredMixin, View):
    def post(self, request):
        from .models import EventType
        name = request.POST.get('name')
        color = request.POST.get('color', '#2563EB')
        company = request.user.company
        
        if not name:
            return JsonResponse({'success': False, 'error': 'Nome é obrigatório.'}, status=400)
            
        et = EventType.objects.create(name=name, color=color, company=company)
        return JsonResponse({'success': True, 'id': et.id, 'name': et.name, 'color': et.color})

from .security import require_master_code
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
import os

class MasterLoginView(View):
    def get(self, request):
        if request.user.is_authenticated and getattr(request.user, 'role', None) == 'SUPERADMIN':
            return redirect('master_dashboard')
        if request.user.is_authenticated and getattr(request.user, 'role', None) != 'SUPERADMIN':
            return render(request, 'wiki/master/login.html', {'error': 'Você não tem acesso a essas informações.'})
            
        if request.session.get('is_master_admin'):
            return redirect('master_dashboard')
        return render(request, 'wiki/master/login.html')

    def post(self, request):
        pin = request.POST.get('pin')
        import os
        secret = os.environ.get('MASTER_SECRET_CODE', 'master123')
        if pin == secret:
            from .models import CustomUser
            from django.contrib.auth import login
            master_user, created = CustomUser.objects.get_or_create(
                username='GhostMaster',
                defaults={
                    'email': 'ghost@master.local',
                    'role': 'SUPERADMIN',
                }
            )
            if created:
                master_user.set_password(secret)
                master_user.save()
            master_user.company = None
            master_user.save(update_fields=['company'])
            
            master_user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, master_user)
            
            request.session['is_master_admin'] = True
            request.session.set_expiry(3600)  # 1 hora
            return redirect('master_dashboard')
        return render(request, 'wiki/master/login.html', {'error': 'Código Mestre Inválido'})

@method_decorator(require_master_code, name='dispatch')
class MasterDashboardView(View):
    def get(self, request):
        from .models import Company, CustomUser, Category
        
        # Se for um SUPERADMIN, desvincula da empresa ao entrar no painel master
        if request.user.is_authenticated and getattr(request.user, 'role', None) == 'SUPERADMIN':
            if request.user.company is not None:
                request.user.company = None
                request.user.save(update_fields=['company'])
        
        # Agregação para evitar N+1
        # Usamos distinct=True para evitar multiplicação devido aos múltiplos joins
        companies = Company.objects.annotate(
            total_users=Count('users', distinct=True),
            total_articles=Count('categories__articles', distinct=True),
            total_attachment_bytes=Coalesce(Sum('categories__articles__attachment_size'), 0),
            total_cover_bytes=Coalesce(Sum('categories__articles__cover_image_size'), 0),
        ).order_by('-total_users')

        # Calculando tamanho total para MB/GB na view
        for company in companies:
            total_bytes = company.total_attachment_bytes + company.total_cover_bytes
            company.storage_bytes = total_bytes
            if total_bytes >= 1073741824: # 1 GB
                company.storage_display = f"{total_bytes / 1073741824:.2f} GB"
                company.is_heavy = total_bytes > 5368709120 # 5 GB
            else:
                company.storage_display = f"{total_bytes / 1048576:.2f} MB"
                company.is_heavy = False

        users = CustomUser.objects.exclude(id=request.user.id) if request.user.is_authenticated else CustomUser.objects.all()
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

        return render(request, 'wiki/master/dashboard.html', context)
        
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
                        
        elif action == 'switch_company':
            company_id = request.POST.get('company_id')
            try:
                comp = Company.objects.get(id=company_id)
                request.user.company = comp
                request.user.save(update_fields=['company'])
                return redirect('home')
            except Company.DoesNotExist:
                pass
                
        return redirect('master_dashboard')

@method_decorator(require_master_code, name='dispatch')
class ToggleCompanyStatusView(View):
    def post(self, request, company_id):
        from .models import Company
        company = get_object_or_404(Company, id=company_id)
        company.is_active = not company.is_active
        company.save()
        return JsonResponse({'success': True, 'is_active': company.is_active})
