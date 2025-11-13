# app_taller/utils.py
from .models import Usuario

from .models import Usuario

from .models import Usuario

from .models import Usuario

from .models import Usuario

def get_usuario_app_from_request(request):
    """
    Mapea el usuario Django (auth.User) a la tabla Usuario.

    Reglas de mapeo:
    1) Si el email coincide -> usa email.
    2) Si el username tiene formato 'usr_<id>' -> usa ese id de Usuario.
    """
    if not request.user.is_authenticated:
        return None

    user = request.user

    # DEBUG
    print("DEBUG helper: username=", user.username, " email=", user.email)

    # 1) Intentar por email (SIN activo=True)
    email = (user.email or "").strip().lower()
    if email:
        u = Usuario.objects.filter(email__iexact=email).first()
        print("DEBUG helper by email →", u)
        if u:
            return u

    # 2) Intentar por username tipo 'usr_5' → Usuario.id = 5
    username = (user.username or "").strip().lower()
    if username.startswith("usr_"):
        try:
            raw_id = username.split("_", 1)[1]
            uid = int(raw_id)
            u = Usuario.objects.filter(pk=uid).first()
            print("DEBUG helper by usr_ID →", u)
            if u:
                return u
        except (ValueError, IndexError):
            pass

    print("DEBUG helper → no se encontró Usuario")
    return None




def get_user_role_dominio(request):
    """
    Retorna el rol literal del Usuario de tu app (ADMIN, SUPERVISOR, JEFE_TALLER, MECANICO, etc.)
    o cadena vacía si no está.
    """
    u = get_usuario_app_from_request(request)
    return (u.rol if u else "") or ""






MSG = {
    "pwd_reset_ok": (
        "La contraseña temporal para {usuario} ha sido generada correctamente. "
        "Proporcione esta credencial de manera segura al usuario para su próximo inicio de sesión."
    ),

    "user_activated": "La cuenta del usuario ha sido activada correctamente.",
    "user_deactivated": (
        "La cuenta del usuario ha sido deshabilitada. "
        "El usuario no podrá acceder al sistema hasta ser reactivado."
    ),

    "no_permission": (
        "No dispone de los permisos necesarios para realizar esta acción."
    ),

    "saved_ok": "El registro se ha guardado correctamente.",
    "unexpected_error": (
        "Se ha producido un error inesperado. "
        "Vuelva a intentarlo o contacte al administrador si el problema persiste."
    ),

    "invalid_form": (
        "La información ingresada no es válida. Revise los campos señalados."
    ),

    "access_denied": (
        "Su sesión no cuenta con autorización para acceder a este recurso."
    ),
}
