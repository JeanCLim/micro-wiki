import datetime
from django.utils import timezone

class UpdateLastSeenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Update last_seen if it's None or older than 1 minute to avoid excessive DB writes
            now = timezone.now()
            if not request.user.last_seen or now - request.user.last_seen > datetime.timedelta(minutes=1):
                request.user.last_seen = now
                # update_fields avoids triggering full save() and signals
                request.user.save(update_fields=['last_seen'])
                
        response = self.get_response(request)
        return response

from django.shortcuts import redirect
class GlobalSuperadminIsolationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.role == 'SUPERADMIN' and request.user.company is None:
            # Prevent accessing knowledge base routes
            allowed_prefixes = ['/master-control-panel/', '/logout/', '/static/', '/api/', '/admin/']
            if not any(request.path.startswith(p) for p in allowed_prefixes):
                return redirect('master_dashboard')
        return self.get_response(request)
