# app_taller/management/commands/seed.py
import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from faker import Faker

from app_taller.models import (
    Usuario, Taller, Vehiculo, ReservaVehiculo, OrdenTrabajo, TareaOT,
    Repuesto, Inventario, MovimientoRepuesto, SolicitudRepuesto,
    LogEstadoOT, Notificacion, EntregaVehiculo, Emergencia
)

fake = Faker("es_CL")

ROLES = ["ADMIN", "SUPERVISOR", "MECANICO", "CHOFER"]
ESTADOS_OT = ["PENDIENTE", "PROGRAMADA", "EN_PROCESO", "PAUSADA", "FINALIZADA", "CERRADA"]
PRIORIDADES = ["BAJA", "NORMAL", "ALTA"]
TIPOS_MOV = ["ENTRADA", "SALIDA"]

def rut_unique(i):
    # rut simple "10000000-i"
    return f"{10000000+i}-{random.randint(0,9)}"

def email_unique(prefix, i):
    return f"{prefix}{i}@demo.cl".lower()

def patente_unique(i):
    # Formato simple XXYnnn
    letras = "BCDFGHJKLPRSTVWXYZ"
    return f"{random.choice(letras)}{random.choice(letras)}{random.choice(letras)}{random.randint(100,999)}"

def sku_unique(i):
    return f"SKU-{10000+i}"

def numero_ot_unique(i):
    return f"OT-{1000+i}"

class Command(BaseCommand):
    help = "Puebla la base con datos de prueba. Crea al menos N registros por tabla."

    def add_arguments(self, parser):
        parser.add_argument("--n", type=int, default=30, help="Cantidad base por tabla (default 30)")
        parser.add_argument("--reset", action="store_true", help="Borra datos antes de poblar")

    @transaction.atomic
    def handle(self, *args, **opts):
        n = max(30, opts["n"])

        if opts["reset"]:
            self.stdout.write("Eliminando datos previos…")
            # Orden inverso para evitar FK issues
            for m in [MovimientoRepuesto, Inventario, SolicitudRepuesto, TareaOT,
                      LogEstadoOT, EntregaVehiculo, Emergencia, Notificacion,
                      ReservaVehiculo, OrdenTrabajo,
                      Vehiculo, Repuesto, Taller, Usuario]:
                m.objects.all().delete()

        self.stdout.write(self.style.WARNING(f"Generando ~{n} registros por tabla…"))

        # ---------- Usuarios ----------
        usuarios = []
        for i in range(n*2):
            rol = random.choice(ROLES)
            usuarios.append(Usuario(
                rut=rut_unique(i),
                nombre_completo=fake.name(),
                email=email_unique("user", i),
                telefono=f"+56 9 {random.randint(40000000, 99999999)}",
                rol=rol,
                hash_contrasena="demo",
                activo=True,
            ))
        Usuario.objects.bulk_create(usuarios, ignore_conflicts=True)
        usuarios = list(Usuario.objects.all())

        # helpers por rol
        mecanicos = [u for u in usuarios if u.rol == "MECANICO"] or usuarios
        choferes  = [u for u in usuarios if u.rol == "CHOFER"]  or usuarios
        supervisores = [u for u in usuarios if u.rol == "SUPERVISOR"] or usuarios
        admins = [u for u in usuarios if u.rol == "ADMIN"] or usuarios

        # ---------- Talleres ----------
        talleres = []
        regiones = ["Metropolitana", "Valparaíso", "Biobío", "O'Higgins", "Maule", "Coquimbo"]
        for i in range(n):
            talleres.append(Taller(
                nombre=f"Taller {fake.city()}",
                codigo=f"T{i:03d}",
                region=random.choice(regiones),
                direccion=fake.address(),
                telefono=f"+56 2 {random.randint(2000000, 3999999)}",
                activo=True,
            ))
        Taller.objects.bulk_create(talleres, ignore_conflicts=True)
        talleres = list(Taller.objects.all())

        # ---------- Repuestos ----------
        repuestos = []
        for i in range(n):
            repuestos.append(Repuesto(
                sku=sku_unique(i),
                nombre=fake.word().title(),
                descripcion=fake.sentence(nb_words=8),
                unidad=random.choice(["UND", "LT", "KG", "PAR"]),
                precio_costo=round(random.uniform(5_000, 150_000), 2),
                activo=True
            ))
        Repuesto.objects.bulk_create(repuestos, ignore_conflicts=True)
        repuestos = list(Repuesto.objects.all())

        # ---------- Inventarios ----------
        inventarios = []
        for t in talleres:
            subset = random.sample(repuestos, k=min(len(repuestos), random.randint(10, n)))
            for r in subset:
                inventarios.append(Inventario(
                    taller=t, repuesto=r,
                    cantidad_disponible=random.randint(0, 200),
                    nivel_minimo_stock=random.randint(0, 20),
                    nivel_maximo_stock=random.randint(30, 200)
                ))
        Inventario.objects.bulk_create(inventarios, ignore_conflicts=True)

        # ---------- Vehículos ----------
        vehiculos = []
        for i in range(n):
            v = Vehiculo(
                patente=patente_unique(i),
                marca=random.choice(["Toyota", "Ford", "Peugeot", "Hyundai", "Ram", "Kia"]),
                modelo=random.choice(["Ranger", "Partner", "V700", "Van 700", "Tucson", "Boxer"]),
                año_modelo=random.choice([2016, 2018, 2020, 2021, 2022, 2023, 2024]),
                vin=fake.bothify(text="########????????"),
                conductor_actual_id=random.choice(choferes).id,
                estado=random.choice(["OPERATIVO", "TALLER", "FUERA_SERVICIO"])
            )
            vehiculos.append(v)
        Vehiculo.objects.bulk_create(vehiculos, ignore_conflicts=True)
        vehiculos = list(Vehiculo.objects.all())

        # ---------- Reservas ----------
        reservas = []
        for i in range(n):
            v = random.choice(vehiculos)
            t = random.choice(talleres)
            inicio = timezone.now() + timedelta(days=random.randint(0, 20))
            fin = inicio + timedelta(days=random.randint(1, 5))
            reservas.append(ReservaVehiculo(
                vehiculo=v, taller=t,
                fecha_inicio_programada=inicio,
                fecha_fin_programada=fin,
                proposito=fake.sentence(nb_words=5),
                estado=random.choice(["PROGRAMADO", "CONFIRMADO", "CANCELADO"]),
                creado_por=random.choice(supervisores)
            ))
        ReservaVehiculo.objects.bulk_create(reservas, ignore_conflicts=True)

        # ---------- Órdenes de trabajo ----------
        ots = []
        for i in range(n):
            v = random.choice(vehiculos)
            t = random.choice(talleres)
            solicitante = random.choice(supervisores + admins)
            mecanico = random.choice(mecanicos)
            apertura = timezone.now() - timedelta(days=random.randint(0, 30))
            ot = OrdenTrabajo(
                numero_ot=numero_ot_unique(i),
                vehiculo=v, taller=t,
                usuario_solicitante=solicitante,
                mecanico_asignado=mecanico,
                jefe_taller=random.choice(supervisores),
                estado=random.choice(ESTADOS_OT),
                prioridad=random.choice(PRIORIDADES),
                emergencia=random.choice([True, False, False]),
                descripcion_problema=fake.text(max_nb_chars=120),
                diagnostico_inicial=fake.sentence(nb_words=8),
                fecha_apertura=apertura
            )
            ots.append(ot)
        OrdenTrabajo.objects.bulk_create(ots, ignore_conflicts=True)
        ots = list(OrdenTrabajo.objects.all())

        # ---------- Log estados ----------
        logs = []
        for ot in ots:
            cambios = random.randint(1, 3)
            estado = "PENDIENTE"
            for j in range(cambios):
                nuevo = random.choice(ESTADOS_OT)
                logs.append(LogEstadoOT(
                    orden_trabajo=ot,
                    estado_anterior=estado,
                    estado_nuevo=nuevo,
                    cambiado_por=random.choice(supervisores),
                    motivo_cambio=fake.sentence(),
                    fecha_cambio=ot.fecha_apertura + timedelta(hours=3*(j+1))
                ))
                estado = nuevo
        LogEstadoOT.objects.bulk_create(logs, ignore_conflicts=True)

        # ---------- Tareas ----------
        tareas = []
        for ot in ots:
            for _ in range(random.randint(1, 3)):
                tareas.append(TareaOT(
                    orden_trabajo=ot,
                    titulo=f"Tarea {fake.word().title()}",
                    descripcion=fake.sentence(),
                    estado=random.choice(["PENDIENTE", "EN_PROCESO", "HECHA"]),
                    mecanico_asignado=random.choice(mecanicos),
                    horas_estimadas=round(random.uniform(1, 6), 2),
                    horas_reales=round(random.uniform(0.5, 8), 2),
                    fecha_inicio=ot.fecha_apertura + timedelta(hours=random.randint(1, 48))
                ))
        TareaOT.objects.bulk_create(tareas, ignore_conflicts=True)

        # ---------- Solicitudes de repuestos ----------
        sols = []
        for ot in random.sample(ots, k=min(len(ots), n)):
            for _ in range(random.randint(1, 2)):
                r = random.choice(repuestos)
                sols.append(SolicitudRepuesto(
                    orden_trabajo=ot, repuesto=r,
                    cantidad_solicitada=random.randint(1, 5),
                    urgente=random.choice([False, False, True]),
                    estado=random.choice(["SOLICITADA", "APROBADA", "RECIBIDA"]),
                    numero_oc=f"OC-{random.randint(10000,99999)}" if random.choice([0,1]) else None,
                    creado_por=random.choice(supervisores)
                ))
        SolicitudRepuesto.objects.bulk_create(sols, ignore_conflicts=True)

        # ---------- Movimientos de repuestos ----------
        movs = []
        for _ in range(n*2):
            t = random.choice(talleres)
            r = random.choice(repuestos)
            ot = random.choice(ots) if random.choice([0,1]) else None
            movs.append(MovimientoRepuesto(
                taller=t, repuesto=r, orden_trabajo=ot,
                tipo_movimiento=random.choice(TIPOS_MOV),
                cantidad=random.randint(1, 10),
                costo_unitario=r.precio_costo,
                motivo=fake.sentence(),
                movido_por=random.choice(usuarios)
            ))
        MovimientoRepuesto.objects.bulk_create(movs, ignore_conflicts=True)

        # ---------- Notificaciones (demo) ----------
        notifs = []
        for i in range(n):
            notifs.append(Notificacion(
                usuario=random.choice(usuarios),
                titulo=fake.sentence(nb_words=4),
                mensaje=fake.sentence(nb_words=10),
                tipo_notificacion=random.choice(["INFO","ALERTA","ERROR"])
            ))
        Notificacion.objects.bulk_create(notifs, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS("¡Datos de prueba generados con éxito!"))
