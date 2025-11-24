# app_taller/models.py
from django.db import models


# ---------------------------
# Catálogos / Choices
# ---------------------------
class RolUsuario(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    SUPERVISOR = "SUPERVISOR", "Supervisor"
    JEFE_TALLER = "JEFE_TALLER", "Jefe de Taller"
    MECANICO = "MECANICO", "Mecánico"
    CHOFER = "CHOFER", "Chofer"
    RECEPCIONISTA = "RECEPCIONISTA", "Recepcionista"


class EstadoVehiculo(models.TextChoices):
    OPERATIVO = "OPERATIVO", "Operativo"
    EN_TALLER = "EN_TALLER", "En Taller"
    FUERA_SERVICIO = "FUERA_SERVICIO", "Fuera de Servicio"


class EstadoReserva(models.TextChoices):
    PROGRAMADO = "PROGRAMADO", "Programado"
    EN_PROCESO = "EN_PROCESO", "En Proceso"
    CANCELADO = "CANCELADO", "Cancelado"
    COMPLETADO = "COMPLETADO", "Completado"


class EstadoOT(models.TextChoices):
    PENDIENTE = "PENDIENTE", "Pendiente"
    EN_PROCESO = "EN_PROCESO", "En Proceso"
    PAUSADA = "PAUSADA", "Pausada"
    FINALIZADA = "FINALIZADA", "Finalizada"
    CERRADA = "CERRADA", "Cerrada"


class PrioridadOT(models.TextChoices):
    BAJA = "BAJA", "Baja"
    NORMAL = "NORMAL", "Normal"
    ALTA = "ALTA", "Alta"
    CRITICA = "CRITICA", "Crítica" 


class EstadoTarea(models.TextChoices):
    PENDIENTE = "PENDIENTE", "Pendiente"
    EN_PROCESO = "EN_PROCESO", "En Proceso"
    PAUSADA = "PAUSADA", "Pausada"
    TERMINADA = "TERMINADA", "Terminada"


class TipoMovimiento(models.TextChoices):
    ENTRADA = "ENTRADA", "Entrada"
    SALIDA = "SALIDA", "Salida"


class EstadoSolicitud(models.TextChoices):
    SOLICITADA = "SOLICITADA", "Solicitada"
    APROBADA = "APROBADA", "Aprobada"
    RECHAZADA = "RECHAZADA", "Rechazada"
    RECIBIDA = "RECIBIDA", "Recibida"
    CANCELADA = "CANCELADA", "Cancelada"


class TipoAdjunto(models.TextChoices):
    IMG = "IMG", "Imagen"
    PDF = "PDF", "PDF"
    DOC = "DOC", "Documento"
    OTRO = "OTRO", "Otro"


class DireccionEntrega(models.TextChoices):
    ENTRADA = "ENTRADA", "Entrada"
    SALIDA = "SALIDA", "Salida"


class NivelEmergencia(models.TextChoices):
    BAJA = "BAJA", "Baja"
    MEDIA = "MEDIA", "Media"
    ALTA = "ALTA", "Alta"


class TipoNotificacion(models.TextChoices):
    INFO = "INFO", "Info"
    ALERTA = "ALERTA", "Alerta"
    ERROR = "ERROR", "Error"


# ---------------------------
# Modelos
# ---------------------------
class Usuario(models.Model):
    id = models.AutoField(primary_key=True)
    rut = models.CharField(max_length=12, unique=True)
    nombre_completo = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    rol = models.CharField(max_length=20, choices=RolUsuario.choices)
    hash_contrasena = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    taller = models.ForeignKey("Taller", null=True, blank=True, on_delete=models.SET_NULL)
    requiere_cambio_clave = models.BooleanField(default=False)


    class Meta:
        db_table = "usuarios"
        managed = True  #  
        indexes = [
            models.Index(fields=["rol"]),
        ]

    def __str__(self):
        return f"{self.nombre_completo} ({self.rut})"



class Taller(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=10, unique=True)
    region = models.CharField(max_length=50)
    direccion = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "talleres"
        indexes = [
            models.Index(fields=["region"]),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class Vehiculo(models.Model):
    patente = models.CharField(max_length=10, unique=True)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    año_modelo = models.IntegerField(blank=True, null=True)
    vin = models.CharField(max_length=50, blank=True, null=True)
    conductor_actual = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name="vehiculos_asignados"
    )
    estado = models.CharField(max_length=20, choices=EstadoVehiculo.choices, default=EstadoVehiculo.OPERATIVO)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "vehiculos"
        indexes = [
            models.Index(fields=["conductor_actual"]),
            models.Index(fields=["estado"]),
        ]

    def __str__(self):
        return self.patente


class ReservaVehiculo(models.Model):
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)
    taller = models.ForeignKey(Taller, on_delete=models.CASCADE)
    fecha_inicio_programada = models.DateTimeField()
    fecha_fin_programada = models.DateTimeField()
    proposito = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=EstadoReserva.choices, default=EstadoReserva.PROGRAMADO)
    creado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="reservas_creadas")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reservas_vehiculos"
        indexes = [
            models.Index(fields=["vehiculo"]),
            models.Index(fields=["taller"]),
            models.Index(fields=["fecha_inicio_programada", "fecha_fin_programada"]),
            models.Index(fields=["creado_por"]),
        ]









from django.utils import timezone 




class OrdenTrabajo(models.Model):
    
    numero_ot = models.CharField(max_length=20, unique=True)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.PROTECT)
    taller = models.ForeignKey(Taller, on_delete=models.PROTECT)
    usuario_solicitante = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="ots_solicitadas")
    mecanico_asignado = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name="ots_asignadas"
    )
    jefe_taller = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name="ots_jefe_taller"
    )
    estado = models.CharField(max_length=20, choices=EstadoOT.choices, default=EstadoOT.PENDIENTE)
    prioridad = models.CharField(max_length=10, choices=PrioridadOT.choices, default=PrioridadOT.NORMAL)
    emergencia = models.BooleanField(default=False)
    descripcion_problema = models.TextField()
    diagnostico_inicial = models.TextField(blank=True, null=True)
    fecha_apertura = models.DateTimeField(auto_now_add=True)
    fecha_programada = models.DateTimeField(blank=True, null=True)
    fecha_pausa = models.DateTimeField(blank=True, null=True)
    fecha_reanudacion = models.DateTimeField(blank=True, null=True)
    fecha_finalizacion = models.DateTimeField(blank=True, null=True)
    fecha_cierre = models.DateTimeField(blank=True, null=True)
    bloqueado_por_repuestos = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    from decimal import Decimal

    total_repuestos  = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    total_mano_obra  = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    total_ot         = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))



    class Meta:
        db_table = "ordenes_trabajo"
        indexes = [
            models.Index(fields=["vehiculo"]),
            models.Index(fields=["taller"]),
            models.Index(fields=["estado"]),
            models.Index(fields=["mecanico_asignado"]),
            models.Index(fields=["fecha_apertura", "fecha_cierre"]),
            models.Index(fields=["emergencia"]),
        ]

    def __str__(self):
        return self.numero_ot
    
    
    from django.utils import timezone
    def generar_numero_ot():
        # Ej: OT20251028-153045
        return timezone.now().strftime("OT%Y%m%d-%H%M%S")
    

    def supervisor_ultimo(self):
        h = self.historial.order_by("-fecha_cambio").first()
        return h.cambiado_por if h else None





class LogEstadoOT(models.Model):
    orden_trabajo = models.ForeignKey(OrdenTrabajo, on_delete=models.CASCADE)
    estado_anterior = models.CharField(max_length=20, choices=EstadoOT.choices, blank=True, null=True)
    estado_nuevo = models.CharField(max_length=20, choices=EstadoOT.choices)
    cambiado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    motivo_cambio = models.TextField(blank=True, null=True)
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    related_name="historial"

    class Meta:
        db_table = "log_estados_ot"
        indexes = [
            models.Index(fields=["orden_trabajo"]),
            models.Index(fields=["fecha_cambio"]),
            models.Index(fields=["cambiado_por"]),
        ]


class TareaOT(models.Model):
    orden_trabajo = models.ForeignKey(OrdenTrabajo, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=EstadoTarea.choices, default=EstadoTarea.PENDIENTE)
    mecanico_asignado = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name="tareas_asignadas"
    )
    horas_estimadas = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    horas_reales = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    fecha_inicio = models.DateTimeField(blank=True, null=True)
    fecha_fin = models.DateTimeField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tareas_ot"
        indexes = [
            models.Index(fields=["orden_trabajo"]),
            models.Index(fields=["mecanico_asignado"]),
            models.Index(fields=["estado"]),
        ]






















class Repuesto(models.Model):
    sku = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    unidad = models.CharField(max_length=20)
    precio_costo = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    informacion_proveedor = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    categoria = models.CharField(max_length=100, blank=True, null=True)
    stock_actual = models.PositiveIntegerField(default=0)

    

    class Meta:
        db_table = "repuestos"
        indexes = [
            models.Index(fields=["nombre"]),
        ]

    def __str__(self):
        return f"{self.sku} - {self.nombre}"
    
    
    





class Inventario(models.Model):
    taller = models.ForeignKey(Taller, on_delete=models.CASCADE)
    repuesto = models.ForeignKey(Repuesto, on_delete=models.CASCADE)
    cantidad_disponible = models.IntegerField(default=0)
    nivel_minimo_stock = models.IntegerField(default=0)
    nivel_maximo_stock = models.IntegerField(blank=True, null=True)
    fecha_ultimo_reabastecimiento = models.DateTimeField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventarios"
        unique_together = ("taller", "repuesto")
        indexes = [
            models.Index(fields=["taller"]),
            models.Index(fields=["repuesto"]),
        ]


class MovimientoRepuesto(models.Model):
    taller = models.ForeignKey(Taller, on_delete=models.PROTECT)
    repuesto = models.ForeignKey(Repuesto, on_delete=models.PROTECT)
    orden_trabajo = models.ForeignKey(OrdenTrabajo, on_delete=models.SET_NULL, null=True, blank=True)
    tipo_movimiento = models.CharField(max_length=10, choices=TipoMovimiento.choices)
    cantidad = models.IntegerField()
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    motivo = models.TextField(blank=True, null=True)
    movido_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="movimientos_realizados")
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name="movimientos_asignados")

    

    class Meta:
        db_table = "movimientos_repuestos"
        indexes = [
            models.Index(fields=["taller"]),
            models.Index(fields=["repuesto"]),
            models.Index(fields=["orden_trabajo"]),
            models.Index(fields=["fecha_movimiento"]),
            models.Index(fields=["tipo_movimiento"]),
        ]


class SolicitudRepuesto(models.Model):
    orden_trabajo = models.ForeignKey(OrdenTrabajo, on_delete=models.CASCADE)
    repuesto = models.ForeignKey(Repuesto, on_delete=models.PROTECT)
    cantidad_solicitada = models.IntegerField()
    urgente = models.BooleanField(default=False)
    estado = models.CharField(max_length=20, choices=EstadoSolicitud.choices, default=EstadoSolicitud.SOLICITADA)
    numero_oc = models.CharField(max_length=50, blank=True, null=True)
    nombre_proveedor = models.CharField(max_length=200, blank=True, null=True)
    fecha_entrega_estimada = models.DateField(blank=True, null=True)
    creado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "solicitudes_repuestos"
        indexes = [
            models.Index(fields=["orden_trabajo"]),
            models.Index(fields=["repuesto"]),
            models.Index(fields=["estado"]),
            models.Index(fields=["numero_oc"]),
        ]


class ArchivoAdjunto(models.Model):
    tipo_entidad = models.CharField(max_length=20)   # 'OT', 'VEHICULO', etc.
    entidad_id = models.IntegerField()
    tipo_archivo = models.CharField(max_length=20, choices=TipoAdjunto.choices)
    nombre_archivo = models.CharField(max_length=255)
    ruta_archivo = models.CharField(max_length=500)
    tamaño_archivo = models.IntegerField(blank=True, null=True)
    tipo_mime = models.CharField(max_length=100, blank=True, null=True)
    subido_por = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "archivos_adjuntos"
        indexes = [
            models.Index(fields=["tipo_entidad", "entidad_id"]),
            models.Index(fields=["tipo_archivo"]),
            models.Index(fields=["subido_por"]),
        ]


class EntregaVehiculo(models.Model):
    orden_trabajo = models.ForeignKey(OrdenTrabajo, on_delete=models.PROTECT)
    direccion = models.CharField(max_length=10, choices=DireccionEntrega.choices)  # ENTRADA / SALIDA
    conductor = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="entregas_conductor")
    recepcionista = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="entregas_recepcionista")
    datos_firma = models.TextField(blank=True, null=True)
    fecha_firma = models.DateTimeField(auto_now_add=True)
    condicion_vehiculo = models.TextField(blank=True, null=True)
    lectura_odometro = models.IntegerField(blank=True, null=True)
    nivel_combustible = models.CharField(max_length=20, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "entregas_vehiculos"
        indexes = [
            models.Index(fields=["orden_trabajo"]),
            models.Index(fields=["conductor"]),
            models.Index(fields=["recepcionista"]),
            models.Index(fields=["direccion"]),
        ]


class Emergencia(models.Model):
    orden_trabajo = models.OneToOneField(
        OrdenTrabajo,
        on_delete=models.CASCADE,
        related_name="emergencia_detalle",          # ← evita el choque
        related_query_name="emergencia_detalle"     # ← opcional pero prolijo
    )
    descripcion_ubicacion = models.TextField()
    latitud = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    longitud = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)
    mecanico_asignado = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name="emergencias_asignadas"
    )
    eta_minutos = models.IntegerField(blank=True, null=True)
    fecha_llegada_real = models.DateTimeField(blank=True, null=True)
    diagnostico_inicial = models.TextField(blank=True, null=True)
    nivel_emergencia = models.CharField(max_length=10, choices=NivelEmergencia.choices, default=NivelEmergencia.MEDIA)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "emergencias"
        indexes = [
            models.Index(fields=["mecanico_asignado"]),
            models.Index(fields=["nivel_emergencia"]),
        ]



class Notificacion(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    tipo_notificacion = models.CharField(max_length=30, choices=TipoNotificacion.choices)
    tipo_entidad_relacionada = models.CharField(max_length=20, blank=True, null=True)
    entidad_relacionada_id = models.IntegerField(blank=True, null=True)
    leida = models.BooleanField(default=False)
    fecha_lectura = models.DateTimeField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notificaciones"
        indexes = [
            models.Index(fields=["usuario"]),
            models.Index(fields=["leida"]),
            models.Index(fields=["fecha_creacion"]),
            models.Index(fields=["tipo_notificacion"]),
        ]


class LogAuditoria(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=50)
    tipo_entidad = models.CharField(max_length=50, blank=True, null=True)
    entidad_id = models.IntegerField(blank=True, null=True)
    valores_anteriores = models.JSONField(blank=True, null=True)
    valores_nuevos = models.JSONField(blank=True, null=True)
    direccion_ip = models.CharField(max_length=45, blank=True, null=True)  # inet simplificado para SQLite
    agente_usuario = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "log_auditoria"
        indexes = [
            models.Index(fields=["usuario"]),
            models.Index(fields=["tipo_entidad"]),
            models.Index(fields=["fecha_creacion"]),
            models.Index(fields=["accion"]),
        ]



class CategoriaRepuesto(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "categorias_repuestos"
        verbose_name = "Categoría de Repuesto"
        verbose_name_plural = "Categorías de Repuestos"

    def __str__(self):
        return self.nombre
