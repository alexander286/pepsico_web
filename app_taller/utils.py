# app_taller/utils.py
from .models import Usuario

def get_usuario_app_from_request(request):
    """
    Mapea el usuario Django al Usuario de tu app (por email).
    Si no existe, retorna None.
    """
    if not request.user.is_authenticated:
        return None
    return Usuario.objects.filter(email=request.user.email, activo=True).first()

def get_user_role_dominio(request):
    """
    Retorna el rol literal del Usuario de tu app (ADMIN, SUPERVISOR, JEFE_TALLER, MECANICO, etc.)
    o cadena vacía si no está.
    """
    u = get_usuario_app_from_request(request)
    return (u.rol if u else "") or ""
