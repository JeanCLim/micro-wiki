from django.contrib import admin
from .models import Category, Tag, Article, ArticleTemplate

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'category')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(ArticleTemplate)
class ArticleTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'company', 'default_visibility')
    list_filter = ('company', 'default_visibility')
    search_fields = ('title', 'content_html')
