from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import (
    Usuario, Taller, Vehiculo, ReservaVehiculo, OrdenTrabajo, TareaOT,
    Repuesto, Inventario, MovimientoRepuesto, SolicitudRepuesto,
    LogEstadoOT, Notificacion, EntregaVehiculo, Emergencia, ArchivoAdjunto
)

admin.site.register(Usuario)
admin.site.register(Taller)
admin.site.register(Vehiculo)
admin.site.register(ReservaVehiculo)
admin.site.register(OrdenTrabajo)
admin.site.register(TareaOT)
admin.site.register(Repuesto)
admin.site.register(Inventario)
admin.site.register(MovimientoRepuesto)
admin.site.register(SolicitudRepuesto)
admin.site.register(LogEstadoOT)
admin.site.register(Notificacion)
admin.site.register(EntregaVehiculo)
admin.site.register(Emergencia)
admin.site.register(ArchivoAdjunto)
