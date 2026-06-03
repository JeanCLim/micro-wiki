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

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('COMMON', 'Usuário Comum'),
        ('EMPLOYEE', 'Funcionário Comum'),
        ('ADMIN', 'Administrador'),
        ('SUPERADMIN', 'Superadmin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='COMMON')
    employee_code = models.CharField(max_length=20, blank=True, null=True, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name='users')
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
    name = models.CharField(max_length=100)
    slug = models.SlugField()
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
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='articles')
    tags = models.ManyToManyField(Tag, blank=True, related_name='articles')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='articles')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
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
