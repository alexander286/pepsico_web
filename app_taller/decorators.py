from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .views import get_user_role  # ya lo tienes

def role_required(*roles):
    roles = {r.upper() for r in roles}
    def deco(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if get_user_role(request.user) not in roles:
                messages.error(request, 'No tienes permisos para esta acción.')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return deco
