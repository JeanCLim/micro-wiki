from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import bleach

class Company(models.Model):
    name = models.CharField(max_length=100)
    cnpj = models.CharField(max_length=20, unique=True)
    domain = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class WorkspaceSettings(models.Model):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='settings')
    favicon = models.ImageField(upload_to='favicons/', blank=True, null=True)
    
    require_2fa = models.BooleanField(default=False)
    session_timeout_minutes = models.IntegerField(default=120)
    slack_webhook_url = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return f"Configurações - {self.company.name}"

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('COMMON', 'Usuário'),
        ('EMPLOYEE', 'Funcionário'),
        ('ADMIN', 'Supervisor'),
        ('SUPERADMIN', 'Superadmin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='COMMON')
    employee_code = models.CharField(max_length=20, blank=True, null=True, unique=True)
    company = models.ForeignKey('Company', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    dark_mode = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    # Atributos destinados à customização particular da interface.
    primary_color = models.CharField(max_length=7, default='#14B8A6')
    font_family = models.CharField(max_length=20, choices=[
        ('MODERN', 'Inter, sans-serif'),
        ('CLASSIC', 'Merriweather, serif'),
        ('TECHNICAL', 'Fira Code, monospace')
    ], default='MODERN')
    border_style = models.CharField(max_length=15, choices=[
        ('SHARP', '0px'),
        ('ROUNDED', '8px'),
        ('PILL', '9999px')
    ], default='ROUNDED')
    compact_layout = models.BooleanField(default=False)
    
    THEME_CHOICES = (
        ('ENTERPRISE', 'Enterprise Blue'),
        ('SLATE', 'Slate Minimalist'),
        ('NORDIC', 'Nordic Forest'),
        ('SNOW', 'Branco Neve (Minimalista)'),
        ('PEARL', 'Branco Pérola (Quente)'),
        ('SILVER', 'Branco Prata (Frio)'),
    )
    theme_preference = models.CharField(max_length=20, choices=THEME_CHOICES, default='ENTERPRISE')

    last_seen = models.DateTimeField(null=True, blank=True)

    @property
    def is_online(self):
        from django.core.cache import cache
        return cache.get(f"presence_{self.pk}", False)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.pk:
            old_instance = CustomUser.objects.get(pk=self.pk)
            if old_instance.role == 'ADMIN' and self.role != 'ADMIN':
                raise ValidationError("Contas com a qualificação 'Administrador' (ADM) jamais podem ter sua qualificação alterada.")
                
        if self.role == 'ADMIN' and self.company:
            existing_admin = CustomUser.objects.filter(company=self.company, role='ADMIN').exclude(pk=self.pk).exists()
            if existing_admin:
                raise ValidationError("A empresa já possui um Administrador. Cada empresa deve ter estritamente uma única conta de Administrador.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class Category(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(db_index=True)
    description = models.TextField(blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name='categories')
    is_special = models.BooleanField(default=False)

    class Meta:
        unique_together = ('company', 'slug')

    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

class Article(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Rascunho'),
        ('PENDING', 'Aguardando Aprovação'),
        ('APPROVED', 'Aprovado'),
        ('REJECTED', 'Rejeitado'),
    )
    VISIBILITY_CHOICES = (
        ('PUBLIC', 'Público'),
        ('INTERNAL_ONLY', 'Apenas Interno'),
        ('MANAGERS_ONLY', 'Apenas Gestores'),
    )
    title = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(unique=True, db_index=True)
    cover_image = models.ImageField(upload_to='articles/covers/', null=True, blank=True)
    cover_image_size = models.PositiveIntegerField(default=0)
    attachment = models.FileField(upload_to='articles/attachments/', null=True, blank=True)
    attachment_size = models.PositiveIntegerField(default=0)
    content = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='articles')
    tags = models.ManyToManyField(Tag, blank=True, related_name='articles')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='articles')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='PUBLIC')
    version = models.CharField(max_length=20, default="01", blank=True)
    valid_until = models.DateField(null=True, blank=True)
    changes_summary = models.CharField(max_length=200, blank=True)
    responsible_area = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('article_detail', args=[self.slug])

class ArticleTemplate(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='article_templates', null=True, blank=True)
    title = models.CharField(max_length=200)
    content_html = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    default_tags = models.ManyToManyField(Tag, blank=True, related_name='templates')
    default_visibility = models.CharField(max_length=20, choices=Article.VISIBILITY_CHOICES, default='PUBLIC')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class ApprovalNotification(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='notifications')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Aprovação pendente: {self.article.title}"

class SystemUpdate(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    version = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Update {self.version} - {self.title}"

class FavoriteArticle(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'article')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} favoritou {self.article.title}"

class EventType(models.Model):
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#2563EB')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='event_types', null=True, blank=True)

    def __str__(self):
        return self.name

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    event_type = models.ForeignKey(EventType, on_delete=models.CASCADE, related_name='events')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_events')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='events', null=True, blank=True)

    def __str__(self):
        return self.title

class UserArticleAccess(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='article_accesses')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='user_accesses')
    access_count = models.PositiveIntegerField(default=1)
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'article')

    def __str__(self):
        return f"{self.user.username} acessou {self.article.title} ({self.access_count}x)"


class UserPresence(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='presences')
    session_key = models.CharField(max_length=40, unique=True, db_index=True)
    last_seen = models.DateTimeField(auto_now=True)
    
    @classmethod
    def get_active_sessions_count(cls, user):
        from django.utils import timezone
        import datetime
        threshold = timezone.now() - datetime.timedelta(seconds=15)
        return cls.objects.filter(user=user, last_seen__gte=threshold).count()
