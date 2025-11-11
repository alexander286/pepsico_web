# app_taller/backends.py
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from app_taller.models import Usuario
from django.contrib.auth.hashers import check_password

class UsuarioBackend(BaseBackend):
    """
    Autentica contra la tabla 'usuarios' usando email + hash_contrasena.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            usuario = Usuario.objects.get(email=username)
        except Usuario.DoesNotExist:
            return None

        if not usuario.activo:
            return None

        # Si hash_contrasena está en texto plano (por ejemplo "demo")
        stored = usuario.hash_contrasena
        if stored.startswith('pbkdf2_') or stored.startswith('argon2') or stored.startswith('bcrypt'):
            valido = check_password(password, stored)
        else:
            valido = (password == stored)

        if not valido:
            return None

        # Crea o sincroniza un User local para manejar sesiones de Django
        user, created = User.objects.get_or_create(username=f"usr_{usuario.id}", defaults={
            'email': usuario.email,
            'first_name': usuario.nombre_completo,
            'is_active': usuario.activo,
            'is_staff': usuario.rol.lower() in ['admin', 'supervisor', 'jefe'],
        })

        user.usuario_id = usuario.id  # opcional, para acceder fácilmente
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
