from django.shortcuts import render
import time
from decimal import Decimal
from django.db import OperationalError, transaction
# Create your views here.
from .utils import get_usuario_app_from_request, get_user_role_dominio
from django.utils.crypto import get_random_string
from .messages_catalog import MSG

from django.utils import timezone
from django.conf import settings

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import TemplateView, FormView
from django import forms

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction
from .forms import IngresoForm
from .models import Vehiculo, OrdenTrabajo, Usuario

# views.py (arriba)
from django.db import transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404
from .models import Vehiculo, OrdenTrabajo, Taller, Usuario, EstadoOT, LogEstadoOT, TareaOT


from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.db.models import Q
from django.utils.timezone import make_aware
from datetime import datetime


from django.views.generic import TemplateView
from app_taller.models import OrdenTrabajo
from .utils import get_usuario_app_from_request



from .models import Usuario  # tu modelo con campo 'rol' y 'email'

# ---------- Helpers ----------
def get_user_role(user: User) -> str:
    # Busca el rol en tu tabla Usuario por email (ajusta si usas username)
    u = None
    if user.email:
        u = Usuario.objects.filter(email=user.email).first()
    if not u:
        # fallback: intenta por nombre de usuario si coincide con email en tu tabla
        u = Usuario.objects.filter(email=user.username).first()
    return (u.rol if u and u.rol else 'ADMIN').upper()

def role_to_url(role: str) -> str:
    role = (role or '').upper()
    if role == 'ADMIN':
        return reverse('dashboard_admin')
    if role == 'SUPERVISOR':
        return reverse('dashboard_supervisor')
    if role == 'MECANICO':
        return reverse('dashboard_mecanico')
    if role == 'CHOFER':
        return reverse('dashboard_chofer')
    return reverse('dashboard_admin')

# ---------- Landing ----------
class HomeView(TemplateView):
    template_name = 'app_taller/home.html'






# ---------- Login ----------
class LoginForm(forms.Form):
    username_or_email = forms.CharField(label='Usuario o correo', max_length=150)
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput)

class LoginViewCustom(FormView):
    template_name = 'app_taller/login.html'
    form_class = LoginForm

    def form_valid(self, form):
        ue = form.cleaned_data['username_or_email'].strip()
        pwd = form.cleaned_data['password']

        # Intentar como username
        user = authenticate(self.request, username=ue, password=pwd)
        if not user:
            # Intentar como email
            try:
                u = User.objects.get(email__iexact=ue)
                user = authenticate(self.request, username=u.username, password=pwd)
            except User.DoesNotExist:
                user = None

        if not user:
            messages.error(self.request, 'Credenciales inválidas.')
            return self.form_invalid(form)

        login(self.request, user)
        role = get_user_role(user)
        return redirect(role_to_url(role))





# ---------- Logout ----------
def logout_view(request):
    logout(request)
    return redirect('home')



# ---------- Dashboards por rol (placeholder UI) ----------
# views.py
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.db.models import Count, Q, Sum

from .models import OrdenTrabajo, Usuario
from .utils import get_usuario_app_from_request, get_user_role_dominio  # o donde lo tengas


class AdminDashboard(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "app_taller/dashboard_admin.html"

    # Solo ADMIN / SUPERVISOR JEFE / staff
    def test_func(self):
        rol = (get_user_role_dominio(self.request) or "").upper().strip()
        return (
            rol in {"ADMIN", "JEFE", "JEFE_TALLER", "SUPERVISOR"}
            or self.request.user.is_staff
            or self.request.user.is_superuser
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        request = self.request

        u = get_usuario_app_from_request(request)
        ctx["usuario_app"] = u

        # === KPIs de OTs ===
        qs_ot = OrdenTrabajo.objects.all()

        ctx["kpi_ots"] = {
            "total": qs_ot.count(),
            "en_proceso": qs_ot.filter(estado="EN_PROCESO").count(),
            "pendientes": qs_ot.filter(estado__in=["PENDIENTE", "ASIGNADA"]).count(),
            "cerradas": qs_ot.filter(estado="CERRADA").count(),
            "criticas": qs_ot.filter(prioridad="CRITICA").count()
            if hasattr(OrdenTrabajo, "prioridad")
            else 0,
        }

        # === KPIs de Usuarios ===
        qs_usr = Usuario.objects.all()

        ctx["kpi_users"] = {
            "total": qs_usr.count(),
            "activos": qs_usr.filter(activo=True).count(),
            "inactivos": qs_usr.filter(activo=False).count(),
            "mecanicos": qs_usr.filter(rol__iexact="MECANICO").count(),
            "supervisores": qs_usr.filter(rol__iexact="SUPERVISOR").count(),
        }

        # Últimas OTs para tabla lateral
        ctx["ultimas_ots"] = (
            qs_ot.select_related("vehiculo", "taller")
            .order_by("-fecha_apertura")[:8]
        )

        # Lista de usuarios para administrar
        ctx["usuarios"] = qs_usr.order_by("-activo", "rol", "nombre_completo")

        return ctx
    


from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse


def _es_admin(request):
    rol = (get_user_role_dominio(request) or "").upper().strip()
    return (
        rol in {"ADMIN", "JEFE", "JEFE_TALLER", "SUPERVISOR"}
        or request.user.is_staff
        or request.user.is_superuser
    )


@login_required
def admin_usuario_toggle_activo(request, usuario_id):
    u = get_object_or_404(Usuario, pk=usuario_id)
    u.activo = not u.activo
    u.save(update_fields=["activo"])

    if u.activo:
        messages.success(
            request,
            f"La cuenta de {u.nombre_completo} ha sido **reactivada correctamente**. "
            f"El usuario podrá volver a iniciar sesión con sus credenciales vigentes."
        )
    else:
        messages.warning(
            request,
            f"La cuenta de {u.nombre_completo} ha sido **deshabilitada de forma temporal**. "
            f"El usuario no podrá iniciar sesión hasta que la cuenta sea reactivada por un administrador."
        )

    return redirect("admin_usuarios_panel")



@login_required
def admin_usuario_reset_password(request, usuario_id):
    if not _es_admin(request):
        messages.error(request, "No tienes permisos de administrador.")
        return redirect("dashboard")

    usuario = get_object_or_404(Usuario, pk=usuario_id)

    # Buscamos auth.User por email
    auth_user = User.objects.filter(email=usuario.email).first()

    if not auth_user:
        # Si no existe, lo creamos con username basado en el email
        username_base = usuario.email or f"user_{usuario.id}"
        auth_user, created = User.objects.get_or_create(
            username=username_base,
            defaults={
                "email": usuario.email or "",
                "is_active": usuario.activo,
            },
        )
    else:
        # Si existe pero el email cambió, lo sincronizamos
        if auth_user.email != usuario.email and usuario.email:
            auth_user.email = usuario.email
            auth_user.save(update_fields=["email"])

    # Generamos clave temporal
    # caracteres sin confusos (sin 0/O/l/I)
    temp_pass = get_random_string(
        10,
        'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    )

    auth_user.set_password(temp_pass)
    auth_user.is_active = usuario.activo  # opcional, para alinear estados
    auth_user.save()

    messages.success(
        request,
        f"Contraseña temporal para {usuario.nombre_completo}: {temp_pass}. "
        "Comunícala al usuario para que la cambie al iniciar sesión."
    )

    return redirect("dashboard_admin")


from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

# ...

def es_admin_sistema(request):
    """
    True si es ADMIN del dominio o staff/superuser de Django.
    """
    rol = (get_user_role_dominio(request) or "").upper().strip()
    if rol in {"ADMIN"}:
        return True
    if request.user.is_staff or request.user.is_superuser:
        return True
    return False







from django.db.models import Q

@login_required
def admin_usuarios_panel(request):
    if not es_admin_sistema(request):
        messages.error(request, "No tienes permisos para acceder al panel de administración de usuarios.")
        return redirect("dashboard")

    q = (request.GET.get("q") or "").strip()
    rol_filtro = (request.GET.get("rol") or "").strip()

    usuarios = Usuario.objects.all().order_by("nombre_completo")

    if q:
        usuarios = usuarios.filter(
            Q(nombre_completo__icontains=q)
            | Q(email__icontains=q)
            | Q(rut__icontains=q)
        )

    if rol_filtro:
        usuarios = usuarios.filter(rol__iexact=rol_filtro)

    # roles disponibles (para el select)
    roles_disponibles = (
        Usuario.objects.exclude(rol__isnull=True)
                       .exclude(rol__exact="")
                       .values_list("rol", flat=True)
                       .distinct()
    )

    ctx = {
        "usuario_app": get_usuario_app_from_request(request),
        "usuarios": usuarios,
        "f": {
            "q": q,
            "rol": rol_filtro,
        },
        "roles_disponibles": roles_disponibles,
    }
    return render(request, "app_taller/admin_usuarios.html", ctx)



@login_required
def admin_usuario_cambiar_rol(request, usuario_id):
    if not es_admin_sistema(request):
        messages.error(request, "No tienes permisos para modificar roles de usuario.")
        return redirect("dashboard")

    usuario = get_object_or_404(Usuario, pk=usuario_id)

    if request.method == "POST":
        nuevo_rol = (request.POST.get("rol") or "").strip().upper()
        if not nuevo_rol:
            messages.error(request, "Debes seleccionar un rol válido.")
            return redirect("admin_usuarios_panel")

        usuario.rol = nuevo_rol
        usuario.save(update_fields=["rol"])

        messages.success(
            request,
            f"El rol de {usuario.nombre_completo} ha sido actualizado a «{nuevo_rol}»."
        )
        return redirect("admin_usuarios_panel")

    # Si alguien entra por GET, simplemente redirigimos
    return redirect("admin_usuarios_panel")


from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# ... ya tienes esto arriba, solo asegúrate que User esté importado


@login_required
def admin_usuario_nuevo(request):
    """
    Permite al administrador registrar un nuevo usuario de dominio (Usuario)
    y, si no existe, crearle también una cuenta de acceso (auth.User).
    """
    if not es_admin_sistema(request):
        messages.error(request, "No tienes permisos para crear usuarios en el sistema.")
        return redirect("dashboard")

    if request.method == "POST":
        rut = (request.POST.get("rut") or "").strip()
        nombre = (request.POST.get("nombre_completo") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()
        rol = (request.POST.get("rol") or "").strip().upper()
        taller_id = (request.POST.get("taller") or "").strip()

        # Validaciones simples
        if not rut or not nombre or not email:
            messages.error(request, "Debes completar al menos RUT, nombre completo y correo.")
            return redirect("admin_usuario_nuevo")

        if Usuario.objects.filter(email=email).exists():
            messages.error(
                request,
                "Ya existe un usuario de dominio registrado con ese correo."
            )
            return redirect("admin_usuario_nuevo")

        taller = None
        if taller_id:
            try:
                taller = Taller.objects.get(pk=taller_id)
            except Taller.DoesNotExist:
                messages.error(request, "El taller seleccionado no existe.")
                return redirect("admin_usuario_nuevo")

        # Crear Usuario (dominio)
       # Construimos solo con los campos que EXISTEN en el modelo Usuario
        usuario_kwargs = {
            "rut": rut,
            "nombre_completo": nombre,
            "email": email,
            "rol": rol,
            "activo": True,
        }

        usuario = Usuario.objects.create(**usuario_kwargs)


        # Vincular / crear cuenta de login (auth.User) por correo
        login_user = User.objects.filter(email=email).first()
        temp_pass_msg = None

        if not login_user:
            base_username = email.split("@")[0] or rut.replace(".", "").replace("-", "")
            username = base_username
            i = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{i}"
                i += 1

            # Generar password temporal “suficiente” para demo
            import secrets, string
            alphabet = string.ascii_letters + string.digits
            temp_pass = "".join(secrets.choice(alphabet) for _ in range(10))

            login_user = User.objects.create_user(
                username=username,
                email=email,
                password=temp_pass,
            )

            # Si el rol es ADMIN, marcamos como staff (panel Django si se quiere)
            if rol == "ADMIN":
                login_user.is_staff = True
                login_user.is_superuser = False  # opcional
                login_user.save()

            temp_pass_msg = f"Usuario de acceso: {username} · Clave temporal: {temp_pass}"
        else:
            temp_pass_msg = "Ya existía una cuenta de acceso asociada a este correo."

        messages.success(
            request,
            f"Usuario «{usuario.nombre_completo}» creado correctamente. {temp_pass_msg}"
        )
        return redirect("admin_usuarios_panel")

    # GET: mostrar formulario vacío
    talleres = Taller.objects.all().order_by("nombre")
    roles_disponibles = (
        Usuario.objects.exclude(rol__isnull=True)
                       .exclude(rol__exact="")
                       .values_list("rol", flat=True)
                       .distinct()
    )

    ctx = {
        "usuario_app": get_usuario_app_from_request(request),
        "talleres": talleres,
        "roles_disponibles": roles_disponibles,
    }
    return render(request, "app_taller/admin_usuario_nuevo.html", ctx)

































    

class SupervisorDashboard(TemplateView):
    template_name = 'app_taller/dashboard_supervisor.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["usuario_app"] = get_usuario_app_from_request(self.request)
        qs = (OrdenTrabajo.objects
              .select_related("taller", "mecanico_asignado", "vehiculo")
              .prefetch_related("logestadoot_set"))

        # KPIs básicos
        total = qs.count()
        en_proceso = qs.filter(estado=EstadoOT.EN_PROCESO).count()
        pendientes = qs.filter(estado=EstadoOT.PENDIENTE).count() if hasattr(EstadoOT, "PENDIENTE") else 0
        cerradas = qs.filter(estado=EstadoOT.CERRADA).count() if hasattr(EstadoOT, "CERRADA") else 0

        # Por prioridad
        prio_alta = qs.filter(prioridad=getattr(PrioridadOT, "ALTA", "ALTA")).count() if hasattr(qs.model, "prioridad") else 0
        prio_critica = qs.filter(prioridad=getattr(PrioridadOT, "CRITICA", "CRITICA")).count() if hasattr(qs.model, "prioridad") else 0

        # Últimas acciones (bitácora)
        ult_logs = (LogEstadoOT.objects
                    .select_related("orden_trabajo", "cambiado_por")
                    .order_by("-fecha_cambio")[:10])

        # Tabla “mis OTs recientes”
        recientes = qs.order_by("-fecha_apertura")[:8]

        ctx.update({
            "kpis": {
                "total": total,
                "en_proceso": en_proceso,
                "pendientes": pendientes,
                "cerradas": cerradas,
                "prio_alta": prio_alta,
                "prio_critica": prio_critica,
            },
            "recientes": recientes,
            "ult_logs": ult_logs,
        })
        return ctx

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib import messages

@login_required
def mecanico_dashboard(request):
    # 1) Resolver Usuario de dominio (tabla Usuario)
    u = get_usuario_app_from_request(request)
    print("DEBUG mecanico_dashboard usuario_app:", u)

    if not u:
        messages.warning(
            request,
            "No se pudo resolver tu usuario de taller. "
            "Revisa la vinculación entre tu cuenta y el usuario de dominio."
        )
        qs = OrdenTrabajo.objects.none()
    else:
        # 🔍 Todas las OTs donde este usuario es mecánico asignado
        # Usamos el email para evitar descalces de IDs
        qs = OrdenTrabajo.objects.filter(mecanico_asignado__email=u.email)
        print("DEBUG mecanico_dashboard qs count:", qs.count())
        print(
            "DEBUG mecanico_dashboard OTs:",
            list(qs.values_list("numero_ot", "mecanico_asignado_id", "mecanico_asignado__email", "estado"))
        )

    # 2) KPIs
    kpis = {
        "total": qs.count(),
        "en_proceso": qs.filter(estado="EN_PROCESO").count(),
        "pendientes": qs.filter(estado__in=["PENDIENTE", "ASIGNADA"]).count(),
        "cerradas": qs.filter(estado="CERRADA").count(),
    }
    print("DEBUG mecanico_dashboard kpis:", kpis)

    # 3) Últimas OTs (10) para la tabla
    mis_ots = qs.select_related("vehiculo", "taller").order_by("-fecha_apertura")[:10]

    ctx = {
        "usuario_app": u,
        "kpis": kpis,
        "mis_ots": mis_ots,
    }
    return render(request, "app_taller/dashboard_mecanico.html", ctx)




class ChoferDashboard(TemplateView):
    template_name = 'app_taller/dashboard_chofer.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["usuario_app"] = get_usuario_app_from_request(self.request)
        return ctx


# Entrada genérica: decide destino por rol
def role_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return redirect(role_to_url(get_user_role(request.user)))




from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Usuario

def get_user_role_dominio(request) -> str:
    u = None
    if request.user and request.user.is_authenticated:
        if request.user.email:
            u = Usuario.objects.filter(email__iexact=request.user.email).first()
        if not u:
            u = Usuario.objects.filter(email__iexact=request.user.username).first()
    return (u.rol if u and u.rol else 'ADMIN').upper()













from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import FormView
from django.db import transaction
from .forms import IngresoForm
from .models import Vehiculo, Usuario, OrdenTrabajo












    # ---------- Ingreso de vehículo (chofer) ----------

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.generic import FormView
from .forms import IngresoVehiculoForm
from .models import Vehiculo

class IngresoNuevoView(FormView):
    template_name = "app_taller/ingreso_nuevo.html"
    form_class = IngresoVehiculoForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["usuario_app"] = get_usuario_app_from_request(self.request)
        return kwargs

    def form_valid(self, form):
        # 1) crear/actualizar vehículo
        patente = form.cleaned_data["patente"]
        vehiculo, _ = Vehiculo.objects.get_or_create(patente=patente)
        vehiculo.conductor_actual = form.cleaned_data.get("conductor_actual")
        vehiculo.save()

        # 2) guardar metadatos (en próxima iteración creamos la OT)
        self.request.session["ultimo_ingreso"] = {
            "patente": patente,
            "fecha_hora_ingreso": form.cleaned_data["fecha_hora_ingreso"].isoformat(),
            "taller_id": form.cleaned_data["taller"].id,
            "observaciones": form.cleaned_data.get("observaciones", ""),
        }

        messages.success(self.request, "Ingreso registrado. En el siguiente paso generaremos la OT.")
        return redirect("dashboard_chofer")


    def form_valid(self, form):
            patente = form.cleaned_data["patente"]

            # 1) Vehículo (alta/actualización)
            vehiculo, _ = Vehiculo.objects.get_or_create(patente=patente)

            # actualiza conductor + NUEVOS campos
            vehiculo.conductor_actual = form.cleaned_data.get("conductor_actual")
            marca = form.cleaned_data.get("marca") or vehiculo.marca
            modelo = form.cleaned_data.get("modelo") or vehiculo.modelo
            anio  = form.cleaned_data.get("anio_modelo") or vehiculo.año_modelo

            vehiculo.marca = marca
            vehiculo.modelo = modelo
            vehiculo.año_modelo = anio
            vehiculo.save()


            # 2) Validar si ya hay una OT abierta para este vehículo
            #    (consideramos abiertas: todo excepto 'CERRADO')
            existe_abierta = OrdenTrabajo.objects.filter(
                vehiculo=vehiculo
            ).exclude(estado="CERRADO").exists()

            if existe_abierta:
                form.add_error(
                    "patente",
                    "Ya existe una OT activa para este vehículo. No se puede crear otra."
                )
                return self.form_invalid(form)

            # 3) Generar número de OT simple (000001, 000002, ...)
            siguiente = (OrdenTrabajo.objects.aggregate(m=Max("id"))["m"] or 0) + 1
            numero_ot = f"{siguiente:06d}"

            # 4) Usuario solicitante (tu dominio)
            u = Usuario.objects.filter(email=self.request.user.email).first()

            # 5) Crear la OT en estado 'INGRESADO'
            ot = OrdenTrabajo.objects.create(
                numero_ot=numero_ot,
                vehiculo=vehiculo,
                taller=form.cleaned_data["taller"],
                usuario_solicitante=u,
                estado="INGRESADO",
                prioridad="NORMAL",
                emergencia=False,
                descripcion_problema=form.cleaned_data.get("observaciones", ""),
                fecha_apertura=form.cleaned_data["fecha_hora_ingreso"],
                total_repuestos=0,
                total_mano_obra=0,
                total_ot=0,
            )


            # --- guardar adjuntos si vinieron ---
            from pathlib import Path
            from django.conf import settings
            from .models import ArchivoAdjunto, TipoAdjunto

            files = form.cleaned_data.get("adjuntos") or []
            if files:
                base_dir = Path(settings.MEDIA_ROOT) / "ot" / ot.numero_ot
                base_dir.mkdir(parents=True, exist_ok=True)

                for f in files:
                    ext = ("." + f.name.split(".")[-1]).lower()
                    tipo = TipoAdjunto.IMG if ext in (".jpg", ".jpeg", ".png") else TipoAdjunto.PDF

                    safe_name = f.name.replace(" ", "_")
                    abs_path = base_dir / safe_name
                    with abs_path.open("wb+") as dest:
                        for chunk in f.chunks():
                            dest.write(chunk)

                    ArchivoAdjunto.objects.create(
                        tipo_entidad="OT",
                        entidad_id=ot.id,
                        tipo_archivo=tipo,
                        nombre_archivo=safe_name,
                        ruta_archivo=f"ot/{ot.numero_ot}/{safe_name}",
                        tamaño_archivo=f.size,
                        tipo_mime=f.content_type,
                        subido_por=Usuario.objects.filter(email=self.request.user.email).first(),
                    )


            messages.success(self.request, f"Ingreso registrado. OT #{ot.numero_ot} creada.")
            return redirect("ot_ficha", numero_ot=ot.numero_ot)
    







    from .models import Usuario

def get_usuario_app_from_request(request) -> Usuario | None:
    u = None
    if request.user and request.user.is_authenticated:
        if request.user.email:
            u = Usuario.objects.filter(email__iexact=request.user.email).first()
        if not u:  # fallback: a veces el username es el email
            u = Usuario.objects.filter(email__iexact=request.user.username).first()
    return u










#OT---------------------------------------------------------------------------------

# views.py
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Max
from django.shortcuts import redirect
from django.views.generic import FormView

from .forms import IngresoVehiculoForm
from .models import Vehiculo, OrdenTrabajo, Usuario

def get_usuario_app_from_request(request) -> Usuario | None:
    u = None
    if request.user and request.user.is_authenticated:
        if request.user.email:
            u = Usuario.objects.filter(email__iexact=request.user.email).first()
        if not u:  # fallback: a veces el username es el email
            u = Usuario.objects.filter(email__iexact=request.user.username).first()
    return u

class IngresoNuevoView(LoginRequiredMixin, FormView):
    template_name = "app_taller/ingreso_nuevo.html"
    form_class = IngresoVehiculoForm

    def form_valid(self, form):
        patente = form.cleaned_data["patente"].strip().upper()

        with transaction.atomic():
            # 1) Vehículo (alta/actualización)
            vehiculo, _ = Vehiculo.objects.get_or_create(
                patente=patente,
                defaults={"marca": "", "modelo": ""}
            ) 

            from .models import EstadoOT  # si aún no lo tienes importado arriba

            # ----- NUEVO: persistir marca / modelo / año_modelo -----
            marca  = form.cleaned_data.get("marca") or ""
            modelo = form.cleaned_data.get("modelo") or ""
            anio   = form.cleaned_data.get("anio_modelo")  # puede venir como str si es ChoiceField

            # si se crea por primera vez, usa defaults con los valores reales
            if _:
                # ya se creó con defaults; actualiza si el form trae datos
                updates = []
                if marca and vehiculo.marca != marca:
                    vehiculo.marca = marca; updates.append("marca")
                if modelo and vehiculo.modelo != modelo:
                    vehiculo.modelo = modelo; updates.append("modelo")
                if anio and vehiculo.año_modelo != int(anio):
                    vehiculo.año_modelo = int(anio); updates.append("año_modelo")
                if updates:
                    vehiculo.save(update_fields=updates)
            else:
                # ya existía: actualizar sólo si hay cambios
                updates = []
                if marca and vehiculo.marca != marca:
                    vehiculo.marca = marca; updates.append("marca")
                if modelo and vehiculo.modelo != modelo:
                    vehiculo.modelo = modelo; updates.append("modelo")
                if anio and vehiculo.año_modelo != int(anio):
                    vehiculo.año_modelo = int(anio); updates.append("año_modelo")
                if updates:
                    vehiculo.save(update_fields=updates)
            # ---------------------------------------------




            conductor = form.cleaned_data.get("conductor_actual")
            if conductor and vehiculo.conductor_actual_id != (conductor.id if conductor else None):
                vehiculo.conductor_actual = conductor
                vehiculo.save(update_fields=["conductor_actual"])

            # 2) Verificar si ya hay OT abierta para este vehículo (todo excepto CERRADO)
            # 2) Verificar si ya hay OT abierta para este vehículo
            existe_abierta = (
                OrdenTrabajo.objects
                .filter(vehiculo=vehiculo)
                .exclude(estado__in=[EstadoOT.CERRADA, "CERRADO"])  # cubre variantes
                .exists()
)

            if existe_abierta:
                form.add_error(
                    "patente",
                    "Ya existe una OT activa para este vehículo. No se puede crear otra."
                )
                return self.form_invalid(form)

            # 3) Usuario solicitante de tu dominio
            solicitante = get_usuario_app_from_request(self.request)
            if not solicitante:
                messages.error(self.request, "No se encontró el Usuario vinculado a tu cuenta.")
                return redirect("dashboard_chofer")

            # 4) Generar número de OT simple incremental: 000001, 000002, ...
            siguiente = (OrdenTrabajo.objects.aggregate(m=Max("id"))["m"] or 0) + 1
            numero_ot = f"{siguiente:06d}"

            # 5) Crear la OT
            ot = OrdenTrabajo.objects.create(
                numero_ot=numero_ot,
                vehiculo=vehiculo,
                taller=form.cleaned_data["taller"],
                usuario_solicitante=solicitante,
                estado=EstadoOT.PENDIENTE,
                prioridad="NORMAL",
                emergencia=False,
                descripcion_problema=form.cleaned_data.get("observaciones", ""),
                fecha_apertura=form.cleaned_data["fecha_hora_ingreso"],
            )

        messages.success(self.request, f"Ingreso registrado. OT #{ot.numero_ot} creada.")
        # Por ahora volvemos al dashboard del chofer; luego apuntaremos a la ficha de la OT
        return redirect("dashboard_chofer")

    def form_invalid(self, form):
        messages.error(self.request, "Revisa los errores del formulario.")
        return super().form_invalid(form)















from django.db.models import Prefetch
from urllib.parse import urlencode

# vista ot
class OTListView(LoginRequiredMixin, ListView):
    model = OrdenTrabajo
    template_name = "app_taller/ot_list.html"
    context_object_name = "ots"
    paginate_by = 25

    def get_queryset(self):
        qs = (OrdenTrabajo.objects
              .select_related("vehiculo", "taller", "mecanico_asignado")
              .prefetch_related(
              Prefetch(
                  "logestadoot_set",  # ← nombre inverso por defecto
                  queryset=LogEstadoOT.objects
                      .select_related("cambiado_por")
                      .order_by("-fecha_cambio"),
                  to_attr="hist"      # ← en la template sigues usando ot.hist.0...
              )
          ))

    



        # Filtros GET: ?q=&estado=&taller=&mecanico=&fdesde=&fhasta=
        q = self.request.GET.get("q", "").strip()
        estado = self.request.GET.get("estado", "").strip()
        taller_id = self.request.GET.get("taller", "").strip()
        mec_id = self.request.GET.get("mecanico", "").strip()
        fdesde = self.request.GET.get("fdesde", "").strip()
        fhasta = self.request.GET.get("fhasta", "").strip()

        prio     = self.request.GET.get("prioridad", "").strip()
        if prio:
            qs = qs.filter(prioridad=prio)

        if q:
            qs = qs.filter(
                Q(numero_ot__icontains=q) |
                Q(vehiculo__patente__icontains=q)
            )
        estado = self.request.GET.get("estado", "").strip()
        if estado:
            qs = qs.filter(estado=estado)

        taller_id = self.request.GET.get("taller", "").strip()
        if taller_id:
            qs = qs.filter(taller_id=taller_id)

        mec_id = self.request.GET.get("mecanico", "").strip()
        if mec_id:
            qs = qs.filter(mecanico_asignado_id=mec_id)
    


        # rango fechas sobre fecha_apertura
        def parse_dt(s):
            try:
                # formato: dd-mm-yyyy hh:mm o dd-mm-yyyy
                for fmt in ("%d-%m-%Y %H:%M", "%d-%m-%Y"):
                    try:
                        return make_aware(datetime.strptime(s, fmt))
                    except ValueError:
                        pass
            except Exception:
                return None
            return None

        dt_desde = parse_dt(fdesde) if fdesde else None
        dt_hasta = parse_dt(fhasta) if fhasta else None

        if dt_desde:
            qs = qs.filter(fecha_apertura__gte=dt_desde)
        if dt_hasta:
            qs = qs.filter(fecha_apertura__lte=dt_hasta)

        return qs.order_by("-fecha_apertura")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        role = get_user_role_dominio(self.request)
        ctx["soy_supervisor"] = role in ("ADMIN", "SUPERVISOR", "JEFE_TALLER")
        # Listas para selects
        ctx["mecanicos"] = Usuario.objects.filter(rol="MECANICO", activo=True).order_by("nombre_completo")
        ctx["talleres"]  = Taller.objects.all().order_by("nombre")
        ctx["estados"]   = [(e.value, e.label) for e in EstadoOT]  # choices
        ctx["prioridades"] = [(p.value, p.label) for p in PrioridadOT]
        # Para mantener valores seleccionados en la UI
        ctx["f"] = {
            "q": self.request.GET.get("q", ""),
            "estado": self.request.GET.get("estado", ""),
            "mecanico": self.request.GET.get("mecanico", ""),
            "taller": self.request.GET.get("taller", ""),
            "desde": self.request.GET.get("desde", ""),
            "hasta": self.request.GET.get("hasta", ""),
            "prioridad":self.request.GET.get("prioridad", ""),

        }
        return ctx
    





class OTDetalleView(LoginRequiredMixin, DetailView):
    model = OrdenTrabajo
    template_name = "app_taller/ot_detalle.html"
    context_object_name = "ot"
    slug_field = "numero_ot"
    slug_url_kwarg = "numero_ot"

    def get_queryset(self):
        return (OrdenTrabajo.objects
                .select_related("vehiculo", "taller", "mecanico_asignado", "usuario_solicitante", "jefe_taller"))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["soy_supervisor"] = get_user_role_dominio(self.request) in ("ADMIN","SUPERVISOR","JEFE")

        ot = ctx["ot"]
        ctx["logs"] = LogEstadoOT.objects.filter(orden_trabajo=ot).select_related("cambiado_por").order_by("-fecha_cambio")
        ctx["tareas"] = TareaOT.objects.filter(orden_trabajo=ot).select_related("mecanico_asignado").order_by("-fecha_creacion")
        return ctx



#############################
#############################
##############################
###############################
###############################
##############################
#############################

from .models import OrdenTrabajo, LogEstadoOT, Usuario, EstadoOT

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.views.generic import DetailView
from django.db import transaction

from .models import OrdenTrabajo, LogEstadoOT, Usuario
from .forms import AsignarMecanicoForm, CambiarEstadoForm

from .models import OrdenTrabajo, LogEstadoOT, Usuario, EstadoOT
from django import forms

from .forms import AdjuntoOTForm
from .models import ArchivoAdjunto
from .forms import EntregaRepuestoForm

@method_decorator(login_required, name="dispatch")
class OTDetalleView(DetailView):
    model = OrdenTrabajo
    template_name = "app_taller/ot_detalle.html"
    slug_field = "numero_ot"
    slug_url_kwarg = "numero_ot"
    context_object_name = "ot"

    def get_object(self):
        return get_object_or_404(OrdenTrabajo, numero_ot=self.kwargs["numero_ot"])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_asignar"] = AsignarMecanicoForm()
        ot = ctx["ot"]
        # 👇 Usa el nombre del campo que definiste en el form
        ctx["form_estado"] = CambiarEstadoForm(initial={"nuevo_estado": _norm_estado(self.object.estado)})
        ctx["logs"] = LogEstadoOT.objects.filter(orden_trabajo=self.object).order_by("-fecha_cambio")
        ctx["form_adjuntos"] = AdjuntoOTForm()
        # (opcional) para poblar el select en la plantilla
        ctx["ESTADO_CHOICES"] = EstadoOT.choices

        ctx["form_prioridad"] = CambiarPrioridadForm(initial={"prioridad": self.object.prioridad})
        ctx["form_estado_vehiculo"] = CambiarEstadoVehiculoForm(initial={"estado": self.object.vehiculo.estado})
    
      
        ctx["form_entrega"] = EntregaRepuestoForm()

        #solo acciones por rol
        role = (get_user_role_dominio(self.request) or "").upper().strip()
        ROLES_SUPERVISORES = {"ADMIN", "SUPERVISOR", "JEFE", "JEFE_TALLER"}

        ctx["soy_supervisor"] = (
            role in ROLES_SUPERVISORES
            or getattr(self.request.user, "is_staff", False)
            or getattr(self.request.user, "is_superuser", False)
        )

        u = get_usuario_app_from_request(self.request)
        ctx["soy_mecanico_asignado"] = bool(u and self.object.mecanico_asignado_id == u.id)

        ctx["puede_solicitar_repuesto"] = bool(
            ctx["soy_mecanico_asignado"] or ctx["soy_supervisor"]
        )

        ctx["logs"] = LogEstadoOT.objects.filter(orden_trabajo=self.object).order_by("-fecha_cambio")
        ctx["tareas"] = TareaOT.objects.filter(orden_trabajo=self.object).select_related("mecanico_asignado").order_by("-fecha_creacion")

        adj = (ArchivoAdjunto.objects
           .filter(tipo_entidad="OT", entidad_id=ot.id)
           .order_by("-fecha_subida"))
        ctx["adjuntos"] = adj

        ctx["adjuntos"] = (ArchivoAdjunto.objects
                    .filter(tipo_entidad="OT", entidad_id=ot.id)
                    .order_by("-fecha_subida"))
        
        ctx["form_solic_repuesto"] = SolicitarRepuestoForm()
        ctx["solicitudes_locales"] = (
            SolicitudRepuesto.objects
            .filter(orden_trabajo=ot)
            .select_related("repuesto", "creado_por")
            .order_by("-fecha_creacion")
        )
        
        # Observaciones iniciales
        obs = ctx["tareas"].filter(titulo="OBS_MECANICO").first()
        ctx["obs_mecanico_inicial"] = (obs.descripcion if obs else "")



         # ⏱ Tiempo en estado actual (cronómetro)
        last_log = (LogEstadoOT.objects
                .filter(orden_trabajo=ot)
                .order_by("-fecha_cambio")
                .first())
        inicio_estado_ts = last_log.fecha_cambio if last_log else ot.fecha_apertura
        ctx["inicio_estado_iso"] = inicio_estado_ts.isoformat()




            # Determinar tipo (temporal: usa defecto)
        tipo = DEFAULT_CHECKLIST
        items = CHECKLIST_CATALOGO.get(tipo, [])
        # Estado actual de cada item:
        marcadas = {t.titulo[4:]: t.descripcion for t in TareaOT.objects.filter(orden_trabajo=ot, titulo__startswith="CHK:")}
        # empaquetar
        ctx["checklist"] = [{"code": c, "texto": txt, "estado": marcadas.get(c)} for (c, txt) in items]



        items_qs = TareaOT.objects.filter(orden_trabajo=ot, titulo__startswith="CHK:")
        total_items = items_qs.count()
        ok_items = items_qs.filter(descripcion__iexact="OK").count()
        ctx["chk_total"] = total_items
        ctx["chk_ok"] = ok_items
        ctx["chk_pct"] = round((ok_items * 100 / total_items), 1) if total_items else 0.0

        ctx["movimientos_salida"] = (
            MovimientoRepuesto.objects
            .filter(orden_trabajo=ot, tipo_movimiento="SALIDA")
            .select_related("repuesto")
            .order_by("-fecha_movimiento")
        )

        movs = (MovimientoRepuesto.objects
        .filter(orden_trabajo=ot)
        .select_related("repuesto")
        .order_by("-fecha_movimiento"))

        total_mov = Decimal("0")
        for m in movs:
            unit = m.costo_unitario or (m.repuesto.precio_costo or Decimal("0"))
            m.unit_to_show = unit
            m.subtotal = (m.cantidad or 0) * unit
            total_mov += m.subtotal

        ctx["movs_repuestos"] = movs
        ctx["total_repuestos_ot"] = total_mov

        try:
            inv = InventarioClient()
            ctx["solicitudes_api"] = inv.listar_solicitudes_ot(ot.numero_ot)  # devuelve list[dict]
        except Exception:
            ctx["solicitudes_api"] = []

        return ctx


@login_required
def ot_asignar_mecanico(request, numero_ot):

    role = get_user_role_dominio(request)
    if role not in ("ADMIN", "SUPERVISOR", "JEFE_TALLER"):
        return HttpResponseForbidden("No tienes permiso para asignar mecánicos.")

    

    ot = get_object_or_404(OrdenTrabajo, numero_ot=numero_ot)
    form = AsignarMecanicoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        ot.mecanico_asignado = form.cleaned_data["mecanico"]
        ot.save(update_fields=["mecanico_asignado"])
        usuario=request.user,
        messages.success(request, "Mecánico asignado correctamente.")
        return redirect("ot_detalle", numero_ot=numero_ot)
    messages.error(request, "Revisa el formulario de asignación.")
    return redirect("ot_detalle", numero_ot=numero_ot)


def _norm_estado(val: str) -> str:
    if not val:
        return ''
    v = str(val).strip().upper().replace(' ', '_')
    # Mapear nombres antiguos a los nuevos si aplica
    if v in ('INGRESADO', 'PROGRAMADA'):
        return EstadoOT.PENDIENTE
    return v

FLUJO_VALIDO = {
    EstadoOT.PENDIENTE:  {EstadoOT.EN_PROCESO},
    EstadoOT.EN_PROCESO: {EstadoOT.PAUSADA, EstadoOT.FINALIZADA},
    EstadoOT.PAUSADA:    {EstadoOT.EN_PROCESO},
    EstadoOT.FINALIZADA: {EstadoOT.CERRADA},
    EstadoOT.CERRADA:    set(),
}




from .views import get_usuario_app_from_request

@login_required
def ot_cambiar_estado(request, numero_ot):
    ot = get_object_or_404(OrdenTrabajo, numero_ot=numero_ot)
    form = CambiarEstadoForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        nuevo = form.cleaned_data.get("nuevo_estado") or form.cleaned_data.get("estado")
        motivo = form.cleaned_data.get("motivo", "") or ""

        permitidos = FLUJO_VALIDO.get(ot.estado, set())
        if nuevo not in permitidos:
            messages.error(request, f"Transición inválida desde {ot.estado} a {nuevo}.")
            return redirect("ot_detalle", numero_ot=numero_ot)

        with transaction.atomic():
            anterior = ot.estado
            ot.estado = nuevo
            ot.save(update_fields=["estado"])

            usuario_actual = get_usuario_app_from_request(request)

            LogEstadoOT.objects.create(
                orden_trabajo=ot,
                estado_anterior=anterior,
                estado_nuevo=nuevo,
                cambiado_por=usuario_actual,
                motivo_cambio=motivo
            )

        messages.success(request, f"Estado cambiado a {nuevo}.")
        return redirect("ot_detalle", numero_ot=numero_ot)

    messages.error(request, "Revisa el formulario de cambio de estado.")
    return redirect("ot_detalle", numero_ot=numero_ot)





# vista supervisor 

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView

@method_decorator(login_required, name="dispatch")
class OTSupervisorListView(ListView):
    model = OrdenTrabajo
    template_name = "app_taller/ot_supervisor_list.html"
    context_object_name = "ots"
    paginate_by = 20

    from .models import PrioridadOT  # arriba si no lo tienes
    # views.py (arriba)
    from .models import PrioridadOT



    def get_queryset(self):
        qs = OrdenTrabajo.objects.select_related("vehiculo", "taller", "mecanico_asignado")

        q = self.request.GET.get("q", "").strip()
        estado = self.request.GET.get("estado", "").strip()
        taller_id = self.request.GET.get("taller", "").strip()
        mec_id = self.request.GET.get("mecanico", "").strip()
        
        fdesde = self.request.GET.get("fdesde", "").strip()
        fhasta = self.request.GET.get("fhasta", "").strip()

        if q:
            qs = qs.filter(Q(numero_ot__icontains=q) | Q(vehiculo__patente__icontains=q))
        if estado:
            qs = qs.filter(estado=estado)
        if taller_id:
            qs = qs.filter(taller_id=taller_id)
        if mec_id:
            qs = qs.filter(mecanico_asignado_id=mec_id)



        prio = self.request.GET.get("prioridad", "").strip()
        if prio:
            qs = qs.filter(prioridad=prio)

        

    

        def parse_dt(s):
            try:
                for fmt in ("%d-%m-%Y %H:%M", "%d-%m-%Y"):
                    try:
                        return make_aware(datetime.strptime(s, fmt))
                    except ValueError:
                        pass
            except Exception:
                return None
            return None

        dt_desde = parse_dt(fdesde) if fdesde else None
        dt_hasta = parse_dt(fhasta) if fhasta else None
        if dt_desde:
            qs = qs.filter(fecha_apertura__gte=dt_desde)
        if dt_hasta:
            qs = qs.filter(fecha_apertura__lte=dt_hasta)

        return qs.order_by("-fecha_apertura")


    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["estados"] = [e for e in OrdenTrabajo.objects.values_list("estado", flat=True).distinct()]
        ctx["mecanicos"] = Usuario.objects.filter(rol="MECANICO", activo=True)
        ctx["talleres"] = set(OrdenTrabajo.objects.values_list("taller__nombre", flat=True))
        from .models import EstadoVehiculo, PrioridadOT
        ctx["vehiculo_estados"] = EstadoVehiculo.choices
        ctx["prioridades"] = [(p.value, p.label) for p in PrioridadOT]  # <-- agrega esto
        ctx["f"] = {
            "q": self.request.GET.get("q", ""),
            "estado": self.request.GET.get("estado", ""),
            "mecanico": self.request.GET.get("mecanico", ""),
            "taller": self.request.GET.get("taller", ""),
            "prioridad": self.request.GET.get("prioridad", ""),  # <-- mantiene selección
            "fdesde": self.request.GET.get("fdesde", ""),
            "fhasta": self.request.GET.get("fhasta", ""),
        }
        return ctx





# app_taller/views.py
from .models import Usuario

def get_usuario_app_from_request(request):
    """Devuelve el objeto Usuario vinculado al usuario logeado en Django"""
    u = None
    if request.user.is_authenticated:
        email = request.user.email or request.user.username
        u = Usuario.objects.filter(email__iexact=email).first()
    return u




from django.http import HttpResponseForbidden
from django.db import transaction
from .forms import CambiarEstadoVehiculoForm, CambiarPrioridadForm
from .models import EstadoVehiculo, PrioridadOT


@login_required
def ot_cambiar_prioridad(request, numero_ot):
    ot = get_object_or_404(OrdenTrabajo, numero_ot=numero_ot)

    role = get_user_role_dominio(request)
    if role not in ("ADMIN", "SUPERVISOR", "MECANICO", "JEFE"):
        return HttpResponseForbidden("No tienes permiso para cambiar prioridad.")

    form = CambiarPrioridadForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        nueva = form.cleaned_data["prioridad"]
        if nueva not in dict(PrioridadOT.choices):
            messages.error(request, "Prioridad inválida.")
            return redirect("ot_detalle", numero_ot=numero_ot)

        with transaction.atomic():
            ot.prioridad = nueva
            ot.save(update_fields=["prioridad"])
        messages.success(request, f"Prioridad actualizada a {nueva}.")
        return redirect("ot_detalle", numero_ot=numero_ot)

    messages.error(request, "Revisa el formulario de prioridad.")
    return redirect("ot_detalle", numero_ot=numero_ot)



@login_required
def vehiculo_cambiar_estado(request, numero_ot):
    ot = get_object_or_404(OrdenTrabajo, numero_ot=numero_ot)
    vehiculo = ot.vehiculo

    role = get_user_role_dominio(request)
    if role not in ("ADMIN", "SUPERVISOR", "MECANICO", "JEFE"):
        return HttpResponseForbidden("No tienes permiso para cambiar el estado del vehículo.")

    form = CambiarEstadoVehiculoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        nuevo = form.cleaned_data["estado"]
        if nuevo not in dict(EstadoVehiculo.choices):
            messages.error(request, "Estado de vehículo inválido.")
            return redirect("ot_detalle", numero_ot=numero_ot)

        with transaction.atomic():
            vehiculo.estado = nuevo
            vehiculo.save(update_fields=["estado"])
        messages.success(request, f"Estado del vehículo actualizado a {nuevo}.")
        return redirect("ot_detalle", numero_ot=numero_ot)

    messages.error(request, "Revisa el formulario de estado del vehículo.")
    return redirect("ot_detalle", numero_ot=numero_ot)







from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from pathlib import Path
from mimetypes import guess_type

from .forms import AdjuntoOTForm
from .models import ArchivoAdjunto, TipoAdjunto


from pathlib import Path
from mimetypes import guess_type
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_SIZE = 8 * 1024 * 1024  # 8 MB

@login_required
def ot_subir_adjuntos(request, numero_ot):
    ot = get_object_or_404(OrdenTrabajo, numero_ot=numero_ot)

    role = get_user_role_dominio(request)
    if role not in ("ADMIN", "SUPERVISOR", "MECANICO", "JEFE"):
        return HttpResponseForbidden("No tienes permiso para subir adjuntos.")

    if request.method != "POST":
        return redirect("ot_detalle", numero_ot=numero_ot)

    # Tomamos etiqueta del form
    form = AdjuntoOTForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Revisa el formulario.")
        return redirect("ot_detalle", numero_ot=numero_ot)

    etiqueta = (form.cleaned_data.get("etiqueta") or "").strip()
    files = request.FILES.getlist("archivos")

    # Validaciones básicas
    if not files:
        messages.error(request, "Debes seleccionar al menos un archivo.")
        return redirect("ot_detalle", numero_ot=numero_ot)

    for f in files:
        ext = (Path(f.name).suffix or "").lower()
        if ext not in ALLOWED_EXTS:
            messages.error(request, f"Archivo no permitido: {f.name}")
            return redirect("ot_detalle", numero_ot=numero_ot)
        if f.size > MAX_SIZE:
            messages.error(request, f"{f.name}: excede 8 MB")
            return redirect("ot_detalle", numero_ot=numero_ot)

    # Guardado
    usuario = get_usuario_app_from_request(request)
    base_dir = Path("ot_adjuntos") / str(ot.numero_ot)

    for f in files:
        dest_name = f"{timezone.now().strftime('%Y%m%d_%H%M%S_%f')}_{f.name}"
        rel_path = base_dir / dest_name
        saved_path = default_storage.save(str(rel_path), ContentFile(f.read()))
        url = default_storage.url(saved_path)

        # tipo archivo
        mime, _ = guess_type(f.name)
        ext = (Path(f.name).suffix or "").lower()
        if ext in (".jpg", ".jpeg", ".png"):
            tipo = TipoAdjunto.IMG
        elif ext == ".pdf":
            tipo = TipoAdjunto.PDF
        else:
            tipo = TipoAdjunto.OTRO

        ArchivoAdjunto.objects.create(
            tipo_entidad="OT",
            entidad_id=ot.id,
            tipo_archivo=tipo,
            nombre_archivo=f"{etiqueta + ' - ' if etiqueta else ''}{f.name}",
            ruta_archivo=url,
            tamaño_archivo=f.size,
            tipo_mime=mime or "",
            subido_por=usuario,
        )

    messages.success(request, "Adjuntos subidos correctamente.")
    return redirect("ot_detalle", numero_ot=numero_ot)















# vista mecanico para listar  las ots a su nombre de rol

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from .models import OrdenTrabajo, EstadoOT, PrioridadOT
from .views import get_usuario_app_from_request  

@method_decorator(login_required, name="dispatch")
class OTMecanicoListView(ListView):
    template_name = "app_taller/ot_mecanico_list.html"
    context_object_name = "ots"
    paginate_by = 20

    def get_queryset(self):
        mec = get_usuario_app_from_request(self.request)
        qs = (OrdenTrabajo.objects
              .select_related("vehiculo","taller")
              .filter(mecanico_asignado=mec)
              .exclude(estado=EstadoOT.CERRADA)
              .order_by("-fecha_apertura"))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["prioridades"] = [(p.value, p.label) for p in PrioridadOT]
        return ctx



from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import LogEstadoOT, EstadoOT, MovimientoRepuesto, TipoMovimiento
from .services.inventario_client import InventarioClient


@login_required
def ot_mecanico_accion(request, numero_ot, accion):
    ot = get_object_or_404(OrdenTrabajo, numero_ot=numero_ot)
    u_app = get_usuario_app_from_request(request)
    role = (get_user_role_dominio(request) or "").upper().strip()
    es_supervisor = role in {"ADMIN", "SUPERVISOR", "JEFE", "JEFE_TALLER"} or request.user.is_staff or request.user.is_superuser
    es_mec_asignado = bool(u_app and ot.mecanico_asignado_id == u_app.id)
    if not (es_supervisor or es_mec_asignado):
        return JsonResponse({"ok": False, "msg": "Sin permisos"}, status=403)

    accion = (accion or "").upper().strip()
    nuevo_estado = None
    motivo = request.POST.get("motivo", "").strip()

    if accion == "INICIAR":
        nuevo_estado = EstadoOT.EN_PROCESO
    elif accion == "PAUSAR":
        nuevo_estado = EstadoOT.PAUSADA
        if not motivo:
            return JsonResponse({"ok": False, "msg": "Debes indicar un motivo para pausar."}, status=400)
    elif accion == "REANUDAR":
        nuevo_estado = EstadoOT.EN_PROCESO
    elif accion == "FINALIZAR":
        nuevo_estado = EstadoOT.CERRADO
    else:
        return JsonResponse({"ok": False, "msg": "Acción no reconocida."}, status=400)

    # Si ya está en ese estado, no duplicar
    if _norm_estado(ot.estado) != _norm_estado(nuevo_estado):
        ot.estado = nuevo_estado
        ot.save(update_fields=["estado"])
        LogEstadoOT.objects.create(
            orden_trabajo=ot,
            estado=nuevo_estado,
            motivo=motivo if motivo else None,
            usuario=request.user
        )

    return JsonResponse({
        "ok": True,
        "estado": nuevo_estado,
        "inicio_estado_iso": timezone.now().isoformat(),  # reinicia cronómetro en UI
        "msg": f"OT {accion.title()}."
    })



@login_required
def ot_entregar_repuesto(request, numero_ot):
    ot = get_object_or_404(OrdenTrabajo, numero_ot=numero_ot)
    user = get_usuario_app_from_request(request)
    role = get_user_role_dominio(request)
    if not (user and (ot.mecanico_asignado_id == user.id or role in ("ADMIN", "SUPERVISOR", "JEFE_TALLER"))):
        return HttpResponseForbidden("No tienes permiso para esta OT.")

    if request.method != "POST":
        return redirect("ot_detalle", numero_ot=numero_ot)

    form = EntregaRepuestoForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Datos inválidos para entrega.")
        return redirect("ot_detalle", numero_ot=numero_ot)

    sku = form.cleaned_data["sku"].strip().upper()
    cantidad = form.cleaned_data["cantidad"]

    inv = InventarioClient()
    # 1) (opcional) check stock
    resp = inv.check_stock(sku)
    if not resp.get("ok", False):
        messages.warning(request, f"Inventario no disponible (modo degradado): {resp.get('error','')}")
        modo_degradado = True
    else:
        modo_degradado = False

    # 2) entregar (o “pre-entregar” si estamos degradados)
    entrega_resp = inv.entregar(
        ot=ot.numero_ot,
        taller=ot.taller.codigo if hasattr(ot.taller, "codigo") else str(ot.taller_id),
        items=[Item(sku=sku, cantidad=cantidad)],
        usuario=(user.email if user else "sistema")
    )

    if not entrega_resp.get("ok", False):
        messages.error(request, "Fallo al registrar entrega en Inventario.")
        return redirect("ot_detalle", numero_ot=numero_ot)

    # 3) Registra movimiento local (tus tablas)
    from .models import Repuesto, Taller, MovimientoRepuesto, TipoMovimiento

    rep = Repuesto.objects.filter(sku=sku).first()
    if not rep:
        # crea soft si no existe para no romper flujo
        rep = Repuesto.objects.create(sku=sku, nombre=f"SKU {sku}", unidad="UN")

    MovimientoRepuesto.objects.create(
        taller=ot.taller,
        repuesto=rep,
        orden_trabajo=ot,
        tipo_movimiento=TipoMovimiento.SALIDA,
        cantidad=cantidad,
        motivo="Entrega por API",
        movido_por=user
    )

    messages.success(request, f"Entrega registrada (sku {sku} x {cantidad}).")
    return redirect("ot_detalle", numero_ot=numero_ot)


# views.py (asegúrate de tener estos imports arriba)
from .models import OrdenTrabajo, EstadoOT
from .views import get_usuario_app_from_request  # si está en este mismo archivo, no hace falta
# (ya lo tienes, lo uso igual aquí)

# en la parte de dashboards
class MecanicoDashboard(TemplateView):
    template_name = 'app_taller/dashboard_mecanico.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = get_usuario_app_from_request(self.request)
        if not u:
            ctx["ots_asignadas"] = []
            ctx["kpi"] = {"abiertas": 0, "pausadas": 0, "hoy": 0, "finalizadas_hoy": 0}
            return ctx

        qs = (OrdenTrabajo.objects
              .select_related("vehiculo","taller")
              .filter(mecanico_asignado_id=u.id)
              .order_by("-fecha_apertura"))

        # abiertas = no cerradas
        abiertas = qs.exclude(estado=EstadoOT.CERRADA)
        pausadas = qs.filter(estado=EstadoOT.PAUSADA)

        # “hoy”
        from django.utils import timezone
        now = timezone.localtime()
        inicio_hoy = now.replace(hour=0, minute=0, second=0, microsecond=0)
        fin_hoy = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        hoy = qs.filter(fecha_apertura__range=(inicio_hoy, fin_hoy))

        finalizadas_hoy = qs.filter(
            fecha_finalizacion__isnull=False,
            fecha_finalizacion__range=(inicio_hoy, fin_hoy)
        )

        ctx["ots_asignadas"] = abiertas[:20]  # top 20
        ctx["kpi"] = {
            "abiertas": abiertas.count(),
            "pausadas": pausadas.count(),
            "hoy": hoy.count(),
            "finalizadas_hoy": finalizadas_hoy.count(),
        }
        return ctx









from .forms import SolicitarRepuestoForm
from .forms import SolicitarRepuestoForm
from .models import SolicitudRepuesto, EstadoSolicitud
# views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from .models import OrdenTrabajo, SolicitudRepuesto, Usuario, Repuesto
from .forms import SolicitarRepuestoForm

try:
    from .services.inventario_client import InventarioClient
except Exception:
    InventarioClient = None


from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages


from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
@login_required
@require_POST
@login_required
@require_POST
@login_required

def ot_solicitar_repuesto(request, numero_ot):
    # 1) Solo aceptamos POST
    if request.method != "POST":
        messages.error(request, "Acción no permitida (usa POST).")
        return redirect("ot_detalle", numero_ot=numero_ot)

    ot = get_object_or_404(OrdenTrabajo, numero_ot=numero_ot)

    # 2) Usuario de dominio (obligatorio)
    u = get_usuario_app_from_request(request)
    if not u:
        messages.error(request, "No se pudo identificar al usuario de la aplicación.")
        return redirect("ot_detalle", numero_ot=numero_ot)

    # 3) Permisos: supervisor o mecánico asignado
    role = (get_user_role_dominio(request) or "").upper().strip()
    es_supervisor = role in {"ADMIN", "SUPERVISOR", "JEFE", "JEFE_TALLER"} or request.user.is_staff or request.user.is_superuser
    es_mec_asignado = (ot.mecanico_asignado_id == u.id)
    if not (es_supervisor or es_mec_asignado):
        messages.error(request, "No tienes permisos para solicitar repuestos en esta OT.")
        return redirect("ot_detalle", numero_ot=numero_ot)

    # 4) Valida el form
    form = SolicitarRepuestoForm(request.POST)
    if not form.is_valid():
        for campo, errs in form.errors.items():
            for e in errs:
                messages.error(request, f"{campo}: {e}")
        return redirect("ot_detalle", numero_ot=numero_ot)

    # 5) Mapeo defensivo a tu modelo real
    field_names = {f.name for f in SolicitudRepuesto._meta.get_fields()}
    data = {
        "orden_trabajo": ot,
        "repuesto": form.cleaned_data["repuesto"],
        "creado_por": u,     # <- clave para evitar el NOT NULL
        "estado": "PENDIENTE"
    }

    # cantidad
    cantidad = form.cleaned_data.get("cantidad", 1)
    if "cantidad" in field_names:
        data["cantidad"] = cantidad
    elif "cantidad_solicitada" in field_names:
        data["cantidad_solicitada"] = cantidad
    elif "cantidad_pedida" in field_names:
        data["cantidad_pedida"] = cantidad
    else:
        messages.error(request, "No se encontró un campo de cantidad en el modelo de solicitudes.")
        return redirect("ot_detalle", numero_ot=numero_ot)

    # observación (opcional)
    obs_val = form.cleaned_data.get("observacion") or ""
    if "observacion" in field_names:
        data["observacion"] = obs_val
    elif "observaciones" in field_names:
        data["observaciones"] = obs_val
    elif "nota" in field_names:
        data["nota"] = obs_val
    # si no existe, se omite silenciosamente

    # 6) Crear en BD con transacción
    try:
        with transaction.atomic():
            sol = SolicitudRepuesto.objects.create(**data)
    except IntegrityError as e:
        messages.error(request, f"No se pudo crear la solicitud (integridad de datos): {e}")
        return redirect("ot_detalle", numero_ot=numero_ot)
    except Exception as e:
        messages.error(request, f"Error al crear la solicitud: {e}")
        return redirect("ot_detalle", numero_ot=numero_ot)

    messages.success(request, f"Solicitud de repuesto creada (ID {sol.id}).")
    return redirect("ot_detalle", numero_ot=numero_ot)


from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST

@require_POST
@login_required
@login_required
@require_POST
def ot_guardar_observaciones(request, numero_ot):
    ot = get_object_or_404(OrdenTrabajo, numero_ot=numero_ot)
    u_app = get_usuario_app_from_request(request)
    role = (get_user_role_dominio(request) or "").upper().strip()
    es_supervisor = role in {"ADMIN", "SUPERVISOR", "JEFE", "JEFE_TALLER"} or request.user.is_staff or request.user.is_superuser
    es_mec_asignado = bool(u_app and ot.mecanico_asignado_id == u_app.id)

    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    if not (es_supervisor or es_mec_asignado):
        if is_ajax:
            return JsonResponse({"ok": False, "msg": "Sin permisos"}, status=403)
        messages.error(request, "Sin permisos")
        return redirect("ot_detalle", numero_ot=numero_ot)

    txt = (request.POST.get("obs") or "").strip()
    if not txt:
        if is_ajax:
            return JsonResponse({"ok": False, "msg": "Observación vacía"}, status=400)
        messages.error(request, "Observación vacía")
        return redirect("ot_detalle", numero_ot=numero_ot)

    tarea, _ = TareaOT.objects.get_or_create(
        orden_trabajo=ot, titulo="OBS_MECANICO",
        defaults={"descripcion": txt, "mecanico_asignado": u_app}
    )
    if tarea.descripcion != txt:
        tarea.descripcion = txt
        if u_app and tarea.mecanico_asignado_id != u_app.id:
            tarea.mecanico_asignado = u_app
        tarea.save(update_fields=["descripcion", "mecanico_asignado"])

    if is_ajax:
        return JsonResponse({"ok": True, "msg": "Observaciones guardadas"})
    messages.success(request, "Observaciones guardadas")
    return redirect("ot_detalle", numero_ot=numero_ot)



CHECKLIST_CATALOGO = {
    # clave “tipo_trabajo”: lista de (code, texto)
    "mantenimiento": [
        ("niv-aceite", "Verificar nivel de aceite"),
        ("frenos", "Revisión de frenos"),
        ("luces", "Chequeo de luces"),
    ],
    "neumáticos": [
        ("presion", "Revisar presión de neumáticos"),
        ("desgaste", "Inspección de desgaste"),
    ],
}
DEFAULT_CHECKLIST = "mantenimiento"


from django.views.decorators.http import require_POST

def _perm_mecanico_o_sup(request, ot):
    user = get_usuario_app_from_request(request)
    role = get_user_role_dominio(request)
    return bool(user and (ot.mecanico_asignado_id == user.id or role in ("ADMIN","SUPERVISOR","JEFE_TALLER")))

@login_required
@require_POST
def ot_checklist_toggle(request, numero_ot):
  
    ot = get_object_or_404(OrdenTrabajo, numero_ot=numero_ot)
    u = get_usuario_app_from_request(request)

    role = (get_user_role_dominio(request) or "").upper().strip()
    es_supervisor = role in {"ADMIN", "SUPERVISOR", "JEFE_TALLER"} or request.user.is_staff or request.user.is_superuser
    es_mec = bool(u and ot.mecanico_asignado_id == u.id)
    if not (es_supervisor or es_mec):
        return HttpResponseBadRequest("Sin permisos")

    code = (request.POST.get("code") or "").strip()
    estado = (request.POST.get("estado") or "").strip().upper()
    if not code or estado not in {"OK", "PENDIENTE", "NO_APLICA"}:
        return HttpResponseBadRequest("Parámetros inválidos")

    titulo = f"CHK:{code}"

    with transaction.atomic():
        tarea, _ = TareaOT.objects.get_or_create(
            orden_trabajo=ot,
            titulo=titulo,
            defaults={"descripcion": estado, "mecanico_asignado": u}
        )
        tarea.descripcion = estado
        if u:
            tarea.mecanico_asignado = u
        tarea.save(update_fields=["descripcion", "mecanico_asignado"])

    items = TareaOT.objects.filter(orden_trabajo=ot, titulo__startswith="CHK:")
    total = items.count() or 1
    ok = items.filter(descripcion__iexact="OK").count()
    pct = round(ok * 100 / total, 1)

  
    for intento in range(5):
        try:
            with transaction.atomic():
                tarea.descripcion = estado                  # "OK"/"PENDIENTE"/"NO_APLICA"
                if tarea.mecanico_asignado_id is None and u:
                    tarea.mecanico_asignado = u
                tarea.save(update_fields=["descripcion", "mecanico_asignado"])
            break
        except OperationalError as e:
            if "locked" in str(e).lower():
                time.sleep(0.2 * (intento + 1))  # backoff
                continue
            raise

    return JsonResponse({"ok": ok, "total": total, "pct": pct})



from .models import SolicitudRepuesto, MovimientoRepuesto, TipoMovimiento, EstadoSolicitud, Repuesto
from .services.inventario_client import InventarioClient

from django.conf import settings  # (asegúrate de tenerlo)
from django.utils import timezone
from app_taller.models import MovimientoRepuesto

def _rep_code(rep):
    # Fallbacks robustos para código del repuesto
    for attr in ("codigo", "codigo_interno", "sku"):
        if hasattr(rep, attr) and getattr(rep, attr):
            return getattr(rep, attr)
    return f"ID-{rep.id}"  # último recurso: usa el ID

# --- IMPORTS NECESARIOS (arriba en views.py) ---
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone

from .models import (
    OrdenTrabajo,
    SolicitudRepuesto,
    MovimientoRepuesto,
    Repuesto,
    # si tienes enums/choices, impórtalos:
    # TipoMovimiento, EstadoSolicitud
)


from django.db import IntegrityError

# ---------- Helpers ----------

def _rep_code(rep: Repuesto) -> str:
    """Obtiene un código para el repuesto aunque tu modelo no tenga 'codigo'."""
    for attr in ("codigo", "codigo_interno", "sku"):
        if hasattr(rep, attr):
            val = getattr(rep, attr)
            if val:
                return val
    return f"ID-{rep.id}"

def _mv_fields():
    """Set de nombres de campos que realmente existen en tu MovimientoRepuesto."""
    return {f.name for f in MovimientoRepuesto._meta.get_fields()}

def _resolve_taller(ot, user_app):
    """Devuelve un Taller para cumplir NOT NULL en el movimiento."""
    if getattr(ot, "taller", None):
        return ot.taller
    if user_app and getattr(user_app, "taller", None):
        return user_app.taller
    return None

def _set_if_exists(mov_kwargs: dict, fields: set, key: str, value):
    """Setea mov_kwargs[key] si el campo existe en el modelo."""
    if key in fields and value is not None:
        mov_kwargs[key] = value

# ---------- Vista ----------



@login_required
def ot_confirmar_entrega(request, numero_ot, solicitud_id):
    ot = get_object_or_404(OrdenTrabajo, numero_ot=numero_ot)
    sol = get_object_or_404(SolicitudRepuesto, pk=solicitud_id, orden_trabajo=ot)

    # Permisos: solo supervisor / admin / jefe taller
    rol = (get_user_role_dominio(request) or "").upper().strip()
    es_supervisor = rol in {"ADMIN", "SUPERVISOR", "JEFE", "JEFE_TALLER"} or request.user.is_staff or request.user.is_superuser
    if not es_supervisor:
        messages.error(request, "No tienes permiso para confirmar entregas.")
        return redirect("ot_detalle", numero_ot=numero_ot)

    # Usuario de dominio (para auditoría/movimiento)
    u = get_usuario_app_from_request(request)

    # Datos de la solicitud
    rep = sol.repuesto
    # soporta distintos nombres de campo para cantidad
    cant = (
        getattr(sol, "cantidad", None)
        or getattr(sol, "cantidad_solicitada", None)
        or getattr(sol, "cantidad_pedida", None)
        or 1
    )


    

    # Payload para API de inventario (tolerante a tu modelo local)
    payload = {
        "ot": ot.numero_ot,
        "item_code": _rep_code(rep),                      # usa sku/codigo si existe
        "item_name": getattr(rep, "nombre", str(rep)),   # nombre amigable
        "quantity": cant,
        "solicitud_id": sol.id,
    }

    # 1) Intentar Confirmar contra API
    from django.conf import settings

    api_ok = False
    api_error = None
    try:
        inv = InventarioClient()
        _ = inv.confirmar_entrega(payload)   # respeta el flag internamente
        api_ok = True
    except Exception as e:
        api_error = e
        api_ok = False
# ... (persistencia local como ya tienes)


    # 2) Registrar SIEMPRE movimiento local (éxito o fallback)
    fields = _mv_fields()
    mov_kwargs = {}

    # mapeos obligatorios (usa alternativas si el nombre de campo difiere en tu modelo)
    # orden_trabajo / ot_id
    if "orden_trabajo" in fields:
        mov_kwargs["orden_trabajo"] = ot
    elif "ot" in fields:
        mov_kwargs["ot"] = ot
    elif "orden_trabajo_id" in fields:
        mov_kwargs["orden_trabajo_id"] = ot.id

    # repuesto / item
    if "repuesto" in fields:
        mov_kwargs["repuesto"] = rep
    elif "item" in fields:
        mov_kwargs["item"] = rep
    elif "repuesto_id" in fields:
        mov_kwargs["repuesto_id"] = rep.id

    # cantidad / cantidad_entregada
    if "cantidad" in fields:
        mov_kwargs["cantidad"] = cant
    elif "cantidad_entregada" in fields:
        mov_kwargs["cantidad_entregada"] = cant

    # tipo del movimiento
    for k, v in (
        ("tipo", "ENTREGA"),
        ("tipo_movimiento", "ENTREGA"),
        ("movimiento", "ENTREGA"),
    ):
        _set_if_exists(mov_kwargs, fields, k, v)

    # usuario creador
    for k in ("usuario", "creado_por", "registrado_por"):
        _set_if_exists(mov_kwargs, fields, k, u)

    # timestamp / fecha
    now = timezone.now()
    for k in ("timestamp", "fecha", "fecha_movimiento", "fecha_creacion"):
        _set_if_exists(mov_kwargs, fields, k, now)

    # estado inventario
    estado_inv = "CONFIRMADO" if api_ok else "PENDIENTE"
    for k in ("estado_inventario", "estado_movimiento", "estado"):
        _set_if_exists(mov_kwargs, fields, k, estado_inv)

    # taller (NOT NULL en tu error)
    tall = _resolve_taller(ot, u)
    if not tall:
        messages.error(request, "No se pudo determinar el taller para el movimiento (OT o usuario sin taller).")
        return redirect("ot_detalle", numero_ot=numero_ot)
    if "taller" in fields:
        mov_kwargs["taller"] = tall
    elif "taller_id" in fields:
        mov_kwargs["taller_id"] = tall.id

    # Guarda el movimiento
   # 1) Movimiento en tu BD (usando los nombres reales de tu modelo)
    try:
        mov = MovimientoRepuesto(
            orden_trabajo=ot,
            repuesto=rep,
            cantidad=cant,
            movido_por=u,        # 
        )
        # Si tu modelo tiene 'taller' como NOT NULL, adjúntalo:
        try:
            mov.taller = ot.taller
        except AttributeError:
            # si tu modelo no tiene 'taller', ignora
            pass

        # Si tu modelo tiene 'estado_inventario' y quieres reflejar el estado local:
        try:
            mov.estado_inventario = "CONFIRMADO" if api_ok else "PENDIENTE"
        except AttributeError:
            pass

        mov.save()
    except Exception as e:
        messages.error(request, f"No se pudo registrar el movimiento (integridad de datos): {e}")
        return redirect("ot_detalle", numero_ot=numero_ot)

    # 2) Actualiza estado de la solicitud
    sol.estado = "RECIBIDA" if api_ok else "APROBADA"
    if hasattr(sol, "confirmada_por"):
        sol.confirmada_por = u
    if hasattr(sol, "fecha_confirmacion"):
        sol.fecha_confirmacion = timezone.now()
    sol.save()

    # 3) Actualizar estado de la solicitud local
    # Usa tus choices si existen, sino string plano.
    estado_recibida = getattr(EstadoSolicitud, "RECIBIDA", "RECIBIDA")
    estado_aprobada = getattr(EstadoSolicitud, "APROBADA", "APROBADA")

    sol.estado = estado_recibida if api_ok else estado_aprobada
    if hasattr(sol, "confirmada_por") and u:
        sol.confirmada_por = u
    if hasattr(sol, "fecha_confirmacion"):
        sol.fecha_confirmacion = now

    # Solo actualiza los campos que realmente existan
    update_fields = ["estado"]
    if "confirmada_por" in {f.name for f in sol._meta.get_fields()}:
        update_fields.append("confirmada_por")
    if "fecha_confirmacion" in {f.name for f in sol._meta.get_fields()}:
        update_fields.append("fecha_confirmacion")
    sol.save(update_fields=update_fields)

    # 4) Mensajes al usuario
    if api_ok:
        messages.success(request, f"Entrega confirmada en Inventario. Solicitud #{sol.id} → {estado_recibida}")
    else:
        messages.warning(
            request,
            f"API inventario no disponible ({api_error!s}). "
            f"Movimiento local registrado. Solicitud #{sol.id} → {estado_aprobada} (pendiente de sincronizar)"
        )


    from decimal import Decimal
    from django.db import transaction

# ...

    # 2) Registrar SIEMPRE movimiento local (éxito o fallback) + costear
    try:
        costo_unit = rep.precio_costo or Decimal("0")
    except Exception:
        costo_unit = Decimal("0")

    with transaction.atomic():
        # --- MOVIMIENTO DE SALIDA CON COSTO ---
        mov = MovimientoRepuesto.objects.create(
            taller=ot.taller,                     # NOT NULL en tu modelo
            repuesto=rep,
            orden_trabajo=ot,
            tipo_movimiento="SALIDA",             # usa TipoMovimiento.SALIDA si lo tienes
            cantidad=cant,
            costo_unitario=costo_unit,
            motivo=f"Entrega confirmada de solicitud #{sol.id}",
            movido_por=u,
        )

        # --- ACTUALIZA COSTO ACUMULADO EN LA OT (si el campo existe) ---
        if hasattr(ot, "total_repuestos"):
            try:
                subtotal = (Decimal(cant) * (costo_unit or Decimal("0")))
                ot.total_repuestos = (ot.total_repuestos or Decimal("0")) + subtotal
                ot.save(update_fields=["total_repuestos"])
            except Exception:
                # no detengas el flujo si falla solo el acumulado
                pass

        # --- ACTUALIZA ESTADO DE LA SOLICITUD ---
        estado_recibida = getattr(EstadoSolicitud, "RECIBIDA", "RECIBIDA")
        estado_aprobada = getattr(EstadoSolicitud, "APROBADA", "APROBADA")

        sol.estado = estado_recibida if api_ok else estado_aprobada
        if hasattr(sol, "confirmada_por") and u:
            sol.confirmada_por = u
        if hasattr(sol, "fecha_confirmacion"):
            sol.fecha_confirmacion = timezone.now()

        # solo guarda los campos que existan
        update_fields = ["estado"]
        field_names = {f.name for f in sol._meta.get_fields()}
        if "confirmada_por" in field_names: update_fields.append("confirmada_por")
        if "fecha_confirmacion" in field_names: update_fields.append("fecha_confirmacion")
        sol.save(update_fields=update_fields)




    precio = getattr(rep, "precio_costo", None) or Decimal("0")

    mov = MovimientoRepuesto(
        orden_trabajo=ot,
        repuesto=rep,
        cantidad=cant,
        costo_unitario=precio,   # 👈 guarda snapshot del costo
        movido_por=u,
    )
    try:
        mov.taller = ot.taller
    except AttributeError:
        pass
    try:
        mov.estado_inventario = "CONFIRMADO" if api_ok else "PENDIENTE"
    except AttributeError:
        pass

    mov.save()



        # --- Recalcular totales cacheados de la OT ---
    from django.db.models import F, Sum
    from decimal import Decimal

    agg = MovimientoRepuesto.objects.filter(
        orden_trabajo=ot
    ).aggregate(
        total_repuestos=Sum(F("cantidad") * F("costo_unitario"))
    )

    total_repuestos = agg["total_repuestos"] or Decimal("0")
    ot.total_repuestos = total_repuestos

    # si luego quieres usar mano de obra, aquí la sumarías también
    total_mano_obra = ot.total_mano_obra or Decimal("0")
    ot.total_ot = total_repuestos + total_mano_obra

    ot.save(update_fields=["total_repuestos", "total_ot"])



    return redirect("ot_detalle", numero_ot=numero_ot)










# --- IMPORTS (arriba del archivo) ---
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from .models import (
    OrdenTrabajo, Repuesto, SolicitudRepuesto, MovimientoRepuesto,
    EstadoSolicitud, TipoMovimiento
)
from .utils import get_usuario_app_from_request, get_user_role_dominio  # si lo tienes

# === Crear solicitud de repuesto ===
@login_required
def ot_solicitar_repuesto(request, numero_ot):
    ot = get_object_or_404(OrdenTrabajo, numero_ot=numero_ot)

    # Permisos: mecánico asignado o supervisor
    u = get_usuario_app_from_request(request)  # Usuario (modelo de tu app)
    role = (get_user_role_dominio(request) or "").upper().strip()
    es_supervisor = role in {"ADMIN", "SUPERVISOR", "JEFE", "JEFE_TALLER"} or request.user.is_staff or request.user.is_superuser
    es_mec_asignado = bool(u and ot.mecanico_asignado_id == u.id)

    if not (es_supervisor or es_mec_asignado):
        messages.error(request, "No tienes permisos para solicitar repuestos en esta OT.")
        return redirect("ot_detalle", numero_ot=numero_ot)

    # Validación básica de POST
    repuesto_id = request.POST.get("repuesto")
    cantidad = request.POST.get("cantidad")
    observacion = (request.POST.get("observacion") or "").strip()

    try:
        rep = Repuesto.objects.get(pk=repuesto_id)
    except Repuesto.DoesNotExist:
        messages.error(request, "Repuesto no válido.")
        return redirect("ot_detalle", numero_ot=numero_ot)

    try:
        cantidad_int = int(cantidad)
        if cantidad_int <= 0:
            raise ValueError()
    except Exception:
        messages.error(request, "Cantidad inválida.")
        return redirect("ot_detalle", numero_ot=numero_ot)

    if not u:
        messages.error(request, "No se pudo identificar al usuario de la aplicación (creado_por).")
        return redirect("ot_detalle", numero_ot=numero_ot)

    try:
        with transaction.atomic():
            # Tu modelo usa 'cantidad_solicitada' (no 'cantidad')
            sol = SolicitudRepuesto.objects.create(
                orden_trabajo=ot,
                repuesto=rep,
                cantidad_solicitada=cantidad_int,
                urgente=False,  # o toma desde el form si lo tienes
                estado=EstadoSolicitud.SOLICITADA,
                numero_oc=None,
                nombre_proveedor=None,
                fecha_entrega_estimada=None,
                creado_por=u,
            )
            # Si tu modelo tiene campo de observación (no existe en el que pegaste).
            # Si tienes uno (p. ej. 'observacion' o 'observaciones'), setéalo aquí:
            # sol.observacion = observacion
            # sol.save(update_fields=["observacion"])

        messages.success(request, f"Solicitud de repuesto creada (ID {sol.id}).")
    except IntegrityError as e:
        messages.error(request, f"No se pudo crear la solicitud (integridad de datos).")
    except Exception as e:
        messages.error(request, f"Error al crear la solicitud: {e!s}")

    return redirect("ot_detalle", numero_ot=numero_ot)


# === Confirmar entrega (supervisor) ===
@login_required
def ot_confirmar_entrega(request, numero_ot, solicitud_id):
    ot = get_object_or_404(OrdenTrabajo, numero_ot=numero_ot)
    sol = get_object_or_404(SolicitudRepuesto, pk=solicitud_id, orden_trabajo=ot)

    # Permiso: supervisor (o staff)
    u = get_usuario_app_from_request(request)
    role = (get_user_role_dominio(request) or "").upper().strip()
    es_supervisor = role in {"ADMIN", "SUPERVISOR", "JEFE", "JEFE_TALLER"} or request.user.is_staff or request.user.is_superuser
    if not es_supervisor:
        messages.error(request, "No tienes permiso para confirmar entregas.")
        return redirect("ot_detalle", numero_ot=numero_ot)

    if not u:
        messages.error(request, "No se pudo identificar al usuario de la aplicación (movido_por).")
        return redirect("ot_detalle", numero_ot=numero_ot)

    # Campos obligatorios para MovimientoRepuesto según tu modelo
    if ot.taller_id is None:
        messages.error(request, "La OT no tiene 'taller' asociado. No se puede registrar el movimiento.")
        return redirect("ot_detalle", numero_ot=numero_ot)

    try:
        with transaction.atomic():
            # Registrar movimiento de salida
            MovimientoRepuesto.objects.create(
                taller=ot.taller,
                repuesto=sol.repuesto,
                orden_trabajo=ot,
                tipo_movimiento=TipoMovimiento.SALIDA,  # <- usa tu enum/choices
                cantidad=sol.cantidad_solicitada,
                costo_unitario=None,  # opcional
                motivo=f"Entrega solicitud #{sol.id}",
                movido_por=u,
                # fecha_movimiento se autogenera por auto_now_add
            )

            # Actualizar estado de la solicitud (p.ej. RECIBIDA)
            sol.estado = EstadoSolicitud.RECIBIDA if hasattr(EstadoSolicitud, "RECIBIDA") else EstadoSolicitud.APROBADA
            sol.save(update_fields=["estado", "fecha_actualizacion"])

        messages.success(request, f"Entrega confirmada. Solicitud #{sol.id} actualizada.")
    except IntegrityError:
        messages.error(request, "No se pudo registrar el movimiento (integridad de datos).")
    except Exception as e:
        messages.error(request, f"Error al confirmar entrega: {e!s}")

    return redirect("ot_detalle", numero_ot=numero_ot)


