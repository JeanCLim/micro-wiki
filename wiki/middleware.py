import datetime
from django.utils import timezone

class UpdateLastSeenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Atualiza coluna last_seen a cada um minuto para reduzir excesso de consultas no banco de dados.
            now = timezone.now()
            if not request.user.last_seen or now - request.user.last_seen > datetime.timedelta(minutes=1):
                request.user.last_seen = now
                # Utiliza parâmetro update_fields para evitar sobrecarga de salvamento total da instância e execução de gatilhos.
                request.user.save(update_fields=['last_seen'])
                
        response = self.get_response(request)
        return response

from django.shortcuts import redirect
class GlobalSuperadminIsolationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.role == 'SUPERADMIN' and request.user.company is None:
            # Efetua o bloqueio do acesso às rotas restritas da base de conhecimento.
            allowed_prefixes = ['/master-control-panel/', '/logout/', '/static/', '/api/', '/admin/']
            if not any(request.path.startswith(p) for p in allowed_prefixes):
                return redirect('master_dashboard')
        return self.get_response(request)
