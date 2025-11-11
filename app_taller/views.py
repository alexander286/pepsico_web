from django.shortcuts import render

# Create your views here.

from django.utils import timezone

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
class AdminDashboard(TemplateView):
    template_name = 'app_taller/dashboard_admin.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["usuario_app"] = get_usuario_app_from_request(self.request)
        return ctx

class SupervisorDashboard(TemplateView):
    template_name = 'app_taller/dashboard_supervisor.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["usuario_app"] = get_usuario_app_from_request(self.request)
        return ctx

class MecanicoDashboard(TemplateView):
    template_name = 'app_taller/dashboard_mecanico.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["usuario_app"] = get_usuario_app_from_request(self.request)
        return ctx

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
        ctx["soy_supervisor"] = get_user_role_dominio(self.request) in ("ADMIN", "SUPERVISOR", "JEFE_TALLER")

        u = get_usuario_app_from_request(self.request)
        ctx["soy_mecanico_asignado"] = bool(u and self.object.mecanico_asignado_id == u.id)

        ctx["logs"] = LogEstadoOT.objects.filter(orden_trabajo=self.object).order_by("-fecha_cambio")
        ctx["tareas"] = TareaOT.objects.filter(orden_trabajo=self.object).select_related("mecanico_asignado").order_by("-fecha_creacion")

        adj = (ArchivoAdjunto.objects
           .filter(tipo_entidad="OT", entidad_id=ot.id)
           .order_by("-fecha_subida"))
        ctx["adjuntos"] = adj

        ctx["adjuntos"] = (ArchivoAdjunto.objects
                    .filter(tipo_entidad="OT", entidad_id=ot.id)
                    .order_by("-fecha_subida"))


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
from .services.inventario_client import InventarioClient, Item

@login_required
def ot_mecanico_accion(request, numero_ot, accion):
    ot = get_object_or_404(OrdenTrabajo, numero_ot=numero_ot)
    user = get_usuario_app_from_request(request)
    # Solo el mecánico asignado (o supervisores/admin) pueden operar:
    role = get_user_role_dominio(request)
    if not (ot.mecanico_asignado_id == (user.id if user else None) or role in ("ADMIN","SUPERVISOR","JEFE")):
        return HttpResponseForbidden("No tienes permiso para esta OT.")

    nuevo = None
    motivo = (request.POST.get("motivo") or "").strip()

    if accion == "iniciar" or accion == "reanudar":
        nuevo = EstadoOT.EN_PROCESO
        ot.fecha_reanudacion = timezone.now()
        ot.fecha_pausa = None
    elif accion == "pausar":
        nuevo = EstadoOT.PAUSADA
        ot.fecha_pausa = timezone.now()
        if not motivo:
            messages.error(request, "Debes indicar un motivo de pausa.")
            return redirect("ot_detalle", numero_ot=numero_ot)
    elif accion == "finalizar":
        nuevo = EstadoOT.FINALIZADA
        ot.fecha_finalizacion = timezone.now()
    else:
        messages.error(request, "Acción inválida.")
        return redirect("ot_detalle", numero_ot=numero_ot)

    permitidos = FLUJO_VALIDO.get(ot.estado, set())
    if nuevo not in permitidos:
        messages.error(request, f"Transición inválida desde {ot.estado} a {nuevo}.")
        return redirect("ot_detalle", numero_ot=numero_ot)

    with transaction.atomic():
        anterior = ot.estado
        ot.estado = nuevo
        ot.save(update_fields=["estado","fecha_pausa","fecha_reanudacion","fecha_finalizacion"])

        LogEstadoOT.objects.create(
            orden_trabajo=ot,
            estado_anterior=anterior,
            estado_nuevo=nuevo,
            cambiado_por=user,
            motivo_cambio=motivo
        )

    messages.success(request, f"OT {accion} → {nuevo}.")
    return redirect("ot_detalle", numero_ot=numero_ot)




@login_required
def ot_entregar_repuesto(request, numero_ot):
    ot = get_object_or_404(OrdenTrabajo, numero_ot=numero_ot)
    user = get_usuario_app_from_request(request)
    role = get_user_role_dominio(request)
    if not (ot.mecanico_asignado_id == (user.id if user else None) or role in ("ADMIN","SUPERVISOR","JEFE")):
        return HttpResponseForbidden("No tienes permiso.")

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

class MecanicoDashboard(TemplateView):
    template_name = 'app_taller/dashboard_mecanico.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        usuario = get_usuario_app_from_request(self.request)
        ctx["usuario_app"] = usuario

        # Top 10 OTs del mecánico (todas menos CERRADA)
        if usuario:
            ctx["mis_ots"] = (
                OrdenTrabajo.objects
                .select_related("vehiculo", "taller")
                .filter(mecanico_asignado=usuario)
                .exclude(estado=EstadoOT.CERRADA)
                .order_by("-fecha_apertura")[:10]
            )
        else:
            ctx["mis_ots"] = []

        return ctx
