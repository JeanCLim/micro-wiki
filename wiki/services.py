from django.utils.text import slugify
from django.core.exceptions import ValidationError
from .models import Article, Category, Tag, ApprovalNotification
from .validators import validate_mime_type, validate_file_size_and_role, validate_image_size_strict

def validate_and_process_files(article, request_user, cover_image=None, attachment=None):
    if cover_image:
        validate_mime_type(cover_image)
        if hasattr(cover_image, 'content_type') and not cover_image.content_type.startswith('image/'):
            raise ValidationError("O arquivo de capa deve ser uma imagem válida.")
        validate_image_size_strict(cover_image)
        article.cover_image = cover_image
        
    if attachment:
        validate_mime_type(attachment)
        validate_file_size_and_role(attachment, request_user.role)
        article.attachment = attachment

def create_article(user, title, content, category_id, tags_raw, visibility, action, cover_image=None, attachment=None, version="01", valid_until=None, changes_summary="Criação", responsible_area=""):
    if not title or not content or not category_id:
        raise ValidationError('Campos obrigatórios faltando.')

    slug = slugify(title)
    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        raise ValidationError('Categoria não encontrada.')
        
    status = 'DRAFT'
    if action == 'pending':
        status = 'PENDING'
    if user.role in ['ADMIN', 'SUPERADMIN'] and action == 'publish':
        status = 'APPROVED'

    article = Article(
        title=title,
        slug=slug,
        content=content,
        category=category,
        author=user,
        status=status,
        visibility=visibility,
        version=version,
        valid_until=valid_until if valid_until else None,
        changes_summary=changes_summary,
        responsible_area=responsible_area
    )
    
    validate_and_process_files(article, user, cover_image, attachment)
    
    article.save()

    if tags_raw:
        tag_names = [t.strip() for t in tags_raw.split(',') if t.strip()]
        for t_name in tag_names:
            t_slug = slugify(t_name)
            tag_obj, _ = Tag.objects.get_or_create(slug=t_slug, defaults={'name': t_name})
            article.tags.add(tag_obj)
    
    if status == 'PENDING':
        ApprovalNotification.objects.create(article=article)

    return article

def update_article(article, user, title, content, category_id, tags_raw, visibility, action, cover_image=None, attachment=None, version="01", valid_until=None, changes_summary="Criação", responsible_area=""):
    if not title or not content or not category_id:
        raise ValidationError('Campos obrigatórios faltando.')

    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        raise ValidationError('Categoria não encontrada.')

    article.title = title
    article.slug = slugify(title)
    article.content = content
    article.category = category
    article.visibility = visibility
    article.version = version
    article.valid_until = valid_until if valid_until else None
    article.changes_summary = changes_summary
    article.responsible_area = responsible_area

    status = 'DRAFT'
    if action == 'pending':
        status = 'PENDING'
    if user.role in ['ADMIN', 'SUPERADMIN'] and action == 'publish':
        status = 'APPROVED'
        
    article.status = status
    
    validate_and_process_files(article, user, cover_image, attachment)
    
    article.save()

    article.tags.clear()
    if tags_raw:
        tag_names = [t.strip() for t in tags_raw.split(',') if t.strip()]
        for t_name in tag_names:
            t_slug = slugify(t_name)
            tag_obj, _ = Tag.objects.get_or_create(slug=t_slug, defaults={'name': t_name})
            article.tags.add(tag_obj)
            
    if status == 'PENDING':
        ApprovalNotification.objects.create(article=article)

    return article

def create_category(user, name, is_special_raw):
    if not name:
        raise ValidationError('Nome não informado.')
        
    is_special = is_special_raw in ['on', 'true', '1', True]
    slug = slugify(name)
    company = user.company
    
    if Category.objects.filter(slug=slug, company=company).exists():
        raise ValidationError('Categoria já existe.')
        
    category = Category.objects.create(
        name=name,
        slug=slug,
        company=company,
        is_special=is_special
    )
    return category
