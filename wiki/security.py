from django.shortcuts import redirect
from functools import wraps

def require_master_code(view_func):
    """
    Decorator que gerencia o acesso ao Master Control Panel de acordo com a hierarquia.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Acesso permitido para credencial categorizada como SUPERADMIN.
        if request.user.is_authenticated and getattr(request.user, 'role', None) == 'SUPERADMIN':
            return view_func(request, *args, **kwargs)
            
        # Bloqueio de acesso para credenciais desprovidas de privilégios SUPERADMIN.
        if request.user.is_authenticated and getattr(request.user, 'role', None) != 'SUPERADMIN':
            from django.shortcuts import render
            return render(request, 'wiki/master/login.html', {'error': 'Você não tem acesso a essas informações.'})
            
        # Liberação de roteamento via constatação de sessão de validação (PIN) ativa.
        if request.session.get('is_master_admin'):
            return view_func(request, *args, **kwargs)
            
        # Redirecionamento obrigatório para entrada do PIN devido à ausência de sessão validada.
        return redirect('master_login')
    return _wrapped_view
