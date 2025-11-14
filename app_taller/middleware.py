from django.shortcuts import redirect
from django.urls import reverse


from .utils import get_usuario_app_from_request 


class PasswordChangeRequiredMiddleware:
    """
    Si el Usuario.requiere_cambio_clave es True, obliga a ir a la pantalla
    de cambio de contraseña antes de usar cualquier otra parte del sistema.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user

        if user.is_authenticated:
            path = request.path

            # Rutas donde NO queremos interceptar
            try:
                url_login = reverse("login")
                url_logout = reverse("logout")
                url_cambio = reverse("password_change_forzada")
            except Exception:
                url_login = "/login"
                url_logout = "/logout"
                url_cambio = "/mi-cuenta/cambiar-clave/"

            whitelisted = (
                path.startswith("/static/") or
                path.startswith("/admin/") or
                path == url_login or
                path == url_logout or
                path == url_cambio
            )

            if not whitelisted:
                u = get_usuario_app_from_request(request)
                if u and getattr(u, "requiere_cambio_clave", False):
                    return redirect("password_change_forzada")

        return self.get_response(request)
