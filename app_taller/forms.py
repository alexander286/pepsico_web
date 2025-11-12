# app_taller/forms.py
from django import forms

class LoginForm(forms.Form):
    email = forms.EmailField(label="Correo electrónico")
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)


import re
from django import forms
from django.utils import timezone
from .models import Usuario, Taller, Vehiculo, OrdenTrabajo
from django.core.exceptions import ValidationError
from django.forms.widgets import ClearableFileInput


PATENTE_REGEX = re.compile(r"^([A-Z]{2}\d{2}\d{2}|[A-Z]{4}\d{2}|[A-Z]{2}\d{2}[A-Z]{2})$")
ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_SIZE = 8 * 1024 * 1024  # 8 MB por archivo


class IngresoForm(forms.Form):
    patente = forms.CharField(label="Patente", max_length=10)
    chofer = forms.ModelChoiceField(
        label="Chofer",
        queryset=Usuario.objects.filter(rol="CHOFER", activo=True).order_by("nombre_completo"),
        required=False
    )
    fecha_hora_ingreso = forms.DateTimeField(
        label="Fecha y hora de ingreso",
        initial=timezone.now,
        required=True,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )
    taller = forms.ModelChoiceField(
        label="Taller", queryset=Taller.objects.filter(activo=True).order_by("nombre")
    )
    observaciones = forms.CharField(
        label="Observaciones", max_length=500, required=False, widget=forms.Textarea(attrs={"rows":3})
    )

    def clean_patente(self):
        p = (self.cleaned_data.get("patente") or "").strip().upper().replace(" ", "")
        if not PATENTE_REGEX.match(p):
            raise forms.ValidationError("Formato de patente inválido (Chile histórico/actual).")
        return p

    def clean(self):
        cleaned = super().clean()
        patente = cleaned.get("patente")
        taller = cleaned.get("taller")
        if not patente or not taller:
            return cleaned

        # ¿Existe OT abierta para esta patente?
        ot_abierta = (
            OrdenTrabajo.objects
            .filter(vehiculo__patente=patente)
            .exclude(estado__in=["CERRADO", "CERRADA", "CERRADA"])  # ajusta a tus estados finales
            .exists()
        )
        if ot_abierta:
            self.add_error("patente", "Ya existe una OT activa para esta patente.")

        return cleaned



from django import forms
from .models import Vehiculo, Usuario, RolUsuario

from django import forms
from django.utils import timezone
from .models import Vehiculo, Usuario, Taller, RolUsuario
import re


from django.forms.widgets import ClearableFileInput
from django.core.exceptions import ValidationError
from django.utils import timezone

class MultiFileInput(ClearableFileInput):
    # habilita input múltiple
    allow_multiple_selected = True


RUT_PATENTE_CL = re.compile(r'^([A-Z]{2}\d{4}|[A-Z]{4}\d{2}|[A-Z]{2}\d{2}[A-Z]{2})$')

# app_taller/forms.py
from django.core.exceptions import ValidationError
from django.forms.widgets import ClearableFileInput

# Si ya definiste MultiFileInput arriba, déjalo. Aquí solo añadimos el año y el auto-fill del chofer.
from django.utils import timezone
AÑO_CHOICES = [(y, y) for y in range(1980, timezone.now().year + 2)]
class IngresoVehiculoForm(forms.ModelForm):
    # NUEVOS
    marca = forms.ChoiceField(
        label="Marca",
        required=False,
        choices=[],
    )
    modelo = forms.ChoiceField(
        label="Modelo",
        required=False,
        choices=[],
    )
    anio_modelo = forms.ChoiceField(
        label="Año modelo",
        required=False,
        choices=[("", "Seleccione año")] + [(str(y), str(y)) for y in range(1980, timezone.now().year + 1)],
    )
    adjuntos = forms.FileField(
        label="Adjuntos (JPG/PNG/PDF, máx. 8 MB)",
        required=False,
        widget=MultiFileInput(attrs={"multiple": True, "accept": ".jpg,.jpeg,.png,.pdf"})
    )

    # extras (no pertenecen a Vehiculo)
    fecha_hora_ingreso = forms.DateTimeField(
        label="Fecha y hora de ingreso",
        initial=timezone.now,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )
    taller = forms.ModelChoiceField(
        label="Taller",
        queryset=Taller.objects.all().order_by("nombre")
    )
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "maxlength": 500})
    )

    class Meta:
        model = Vehiculo
        fields = ["patente", "conductor_actual"]  # del modelo
        labels = {"conductor_actual": "Chofer"}
        widgets = {
            "patente": forms.TextInput(attrs={"style": "text-transform:uppercase;"}),
        }

    def __init__(self, *args, **kwargs):
        # recibimos el usuario de tu dominio desde la vista
        self.usuario_app = kwargs.pop("usuario_app", None)
        super().__init__(*args, **kwargs)

        self.fields["conductor_actual"].required = False
        self.fields["conductor_actual"].queryset = (
            Usuario.objects.filter(rol=RolUsuario.CHOFER, activo=True)
            .order_by("nombre_completo")
        )

        # Autocompletar si el logeado es chofer
        if self.usuario_app and getattr(self.usuario_app, "rol", None) == RolUsuario.CHOFER:
            self.fields["conductor_actual"].initial = self.usuario_app.id
            # Si quieres impedir cambio:
            # self.fields["conductor_actual"].disabled = True

        # Actualiza límite superior del año por si corre el tiempo
        self.fields["anio_modelo"].widget.attrs["placeholder"] = str(timezone.now().year)

        from .models import Vehiculo

        # usar import local y post-carga segura
        try:
            from django.apps import apps
            Vehiculo = apps.get_model("app_taller", "Vehiculo")
            marcas = Vehiculo.objects.values_list("marca", flat=True).distinct().exclude(marca__exact="").order_by("marca")
            modelos = Vehiculo.objects.values_list("modelo", flat=True).distinct().exclude(modelo__exact="").order_by("modelo")

            self.fields["marca"].choices = [("", "— Seleccione o escriba —")] + [(m, m) for m in marcas]
            self.fields["modelo"].choices = [("", "— Seleccione o escriba —")] + [(m, m) for m in modelos]
        except Exception:
            # si aún no se cargó el ORM (fase de arranque), deja los combos vacíos
            self.fields["marca"].choices = [("", "— Seleccione —")]
            self.fields["modelo"].choices = [("", "— Seleccione —")]



    def clean_patente(self):
        p = (self.cleaned_data["patente"] or "").upper().replace(" ", "")
        if not RUT_PATENTE_CL.match(p):
            raise forms.ValidationError("Formato de patente no válido (CL).")
        return p

    def clean_adjuntos(self):
        files = self.files.getlist("adjuntos")
        for f in files:
            ext = ("." + f.name.split(".")[-1]).lower()
            if ext not in ALLOWED_EXTS:
                raise ValidationError(f"Archivo no permitido: {f.name}")
            if f.size > MAX_SIZE:
                raise ValidationError(f"{f.name}: excede 8 MB")
        return files






# forms para ot asignatr mecanico y el estado de la ot

from django import forms
from .models import Usuario, OrdenTrabajo, EstadoOT

class AsignarMecanicoForm(forms.Form):
    mecanico = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(rol="MECANICO", activo=True).order_by("nombre_completo"),
        required=True, label="Mecánico"
    )

class CambiarEstadoForm(forms.Form):
    nuevo_estado = forms.ChoiceField(choices=EstadoOT.choices)
    motivo = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))




# app_taller/forms.py
from django import forms
from .models import EstadoVehiculo, PrioridadOT

class CambiarEstadoVehiculoForm(forms.Form):
    estado = forms.ChoiceField(label="Estado del vehículo", choices=EstadoVehiculo.choices)

class CambiarPrioridadForm(forms.Form):
    prioridad = forms.ChoiceField(label="Prioridad", choices=PrioridadOT.choices)






##################################################################################


# --- Subida de adjuntos en ficha de OT ---
class AdjuntoOTForm(forms.Form):
    etiqueta = forms.CharField(label="Etiqueta (opcional)", max_length=100, required=False)






class EntregaRepuestoForm(forms.Form):
    sku = forms.CharField(label="SKU", max_length=50)
    cantidad = forms.IntegerField(label="Cantidad", min_value=1)



from .models import Repuesto 

class SolicitarRepuestoForm(forms.Form):
    repuesto = forms.ModelChoiceField(
        queryset=Repuesto.objects.filter(activo=True).order_by("nombre"),
        label="Repuesto"
    )
    cantidad = forms.IntegerField(min_value=1, label="Cantidad", initial=1)
    urgente = forms.BooleanField(required=False, label="Urgente")
    fecha_entrega_estimada = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    nombre_proveedor = forms.CharField(required=False, max_length=200, label="Proveedor (opcional)")



