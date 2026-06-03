from django.core.exceptions import PermissionDenied
from functools import wraps

def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return view_func(request, *args, **kwargs) # Let LoginRequiredMixin handle it
            if request.user.role in allowed_roles or request.user.role == 'SUPERADMIN':
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapped_view
    return decorator

def global_superadmin_required():
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role == 'SUPERADMIN' and request.user.company is None:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("Acesso negado: Rota restrita ao Master Global.")
        return _wrapped_view
    return decorator
