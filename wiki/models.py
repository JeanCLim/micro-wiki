from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.conf import settings

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
        ('COMMON', 'Usuário Comum'),
        ('EMPLOYEE', 'Funcionário Comum'),
        ('ADMIN', 'Administrador'),
        ('SUPERADMIN', 'Superadmin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='COMMON')
    employee_code = models.CharField(max_length=20, blank=True, null=True, unique=True)
    company = models.ForeignKey('Company', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    dark_mode = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    # Personal UI Customization
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
        from django.utils import timezone
        import datetime
        if self.last_seen:
            return timezone.now() - self.last_seen < datetime.timedelta(minutes=5)
        return False

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
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='articles')
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

    def save(self, *args, **kwargs):
        if self.cover_image:
            try:
                self.cover_image_size = self.cover_image.size
            except Exception:
                pass
        else:
            self.cover_image_size = 0
            
        if self.attachment:
            try:
                self.attachment_size = self.attachment.size
            except Exception:
                pass
        else:
            self.attachment_size = 0
            
        super().save(*args, **kwargs)

class ArticleTemplate(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='article_templates', null=True, blank=True)
    title = models.CharField(max_length=200)
    content_html = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    default_tags = models.CharField(max_length=255, blank=True, help_text="Separadas por vírgula")
    default_visibility = models.CharField(max_length=20, choices=Article.VISIBILITY_CHOICES, default='PUBLIC')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class ApprovalNotification(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='notifications')
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
