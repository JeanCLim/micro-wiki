import magic
from django.core.exceptions import ValidationError

def validate_mime_type(file):
    """
    Valida o real MIME type do arquivo utilizando a biblioteca python-magic.
    Rejeita executáveis e arquivos perigosos camuflados.
    """
    file.seek(0)
    mime_type = magic.from_buffer(file.read(2048), mime=True)
    file.seek(0)

    # Lista negra de mime types perigosos
    forbidden_mimes = [
        'application/x-msdownload',
        'application/x-dosexec',
        'application/x-sh',
        'application/x-bat',
        'application/x-executable',
        'application/vnd.microsoft.portable-executable',
        'application/java-archive',
    ]

    if mime_type in forbidden_mimes:
        raise ValidationError(f"Arquivo não suportado. Tipo detectado ({mime_type}) está bloqueado.")
        
    return mime_type

def validate_file_size_and_role(file, role):
    """
    Aplica limites de tamanho de arquivo (attachment) de acordo com a Role do usuário.
    COMMON/EMPLOYEE: 5MB
    ADMIN/SUPERADMIN: 500MB
    """
    MB = 1024 * 1024
    
    if role in ['ADMIN', 'SUPERADMIN']:
        limit = 500 * MB
        limit_str = '500MB'
    else:
        limit = 5 * MB
        limit_str = '5MB'
        
    if file.size > limit:
        raise ValidationError(f"O arquivo excede o limite máximo para o seu perfil. Seu limite é de {limit_str}.")

def validate_image_size_strict(file):
    """
    Barreira rigorosa para imagens (cover_image).
    Limita em 3MB. Se for maior que isso, o frontend deveria ter comprimido.
    """
    MB = 1024 * 1024
    limit = 3 * MB
    
    if file.size > limit:
        raise ValidationError("A imagem excedeu o limite máximo (3MB). Verifique se o redimensionamento do Frontend ocorreu.")
