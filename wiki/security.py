from django.shortcuts import redirect
from functools import wraps

def require_master_code(view_func):
    """
    Decorator que gerencia o acesso ao Master Control Panel de acordo com a hierarquia.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 1. Conectado como SUPERADMIN (acessa direto)
        if request.user.is_authenticated and getattr(request.user, 'role', None) == 'SUPERADMIN':
            return view_func(request, *args, **kwargs)
            
        # 2. Conectado em conta inferior (acesso negado)
        if request.user.is_authenticated and getattr(request.user, 'role', None) != 'SUPERADMIN':
            from django.shortcuts import render
            return render(request, 'wiki/master/login.html', {'error': 'Você não tem acesso a essas informações.'})
            
        # 3. Não conectado, mas com sessão de PIN ativa
        if request.session.get('is_master_admin'):
            return view_func(request, *args, **kwargs)
            
        # 4. Não conectado e sem PIN (redireciona para login do PIN)
        return redirect('master_login')
    return _wrapped_view
