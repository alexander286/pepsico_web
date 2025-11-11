from django.core.management.base import BaseCommand
from django.utils import timezone
from app_taller.models import Usuario, Taller, Vehiculo, OrdenTrabajo

class Command(BaseCommand):
    help = "Crea datos de prueba básicos para el sistema de talleres"

    def handle(self, *args, **kwargs):
        # Taller
        taller, _ = Taller.objects.get_or_create(
            nombre="Taller Central",
            region="Metropolitana",
            direccion="Av. Siempre Viva 742"
        )

        # Usuarios
        admin, _ = Usuario.objects.get_or_create(
            rut="11111111-1",
            nombre_completo="Administrador General",
            email="admin@demo.cl",
            rol="ADMIN",
            hash_contrasena="1234"
        )

        mecanico, _ = Usuario.objects.get_or_create(
            rut="22222222-2",
            nombre_completo="Carlos Mecanico",
            email="carlos@demo.cl",
            rol="MECANICO",
            hash_contrasena="1234"
        )

        chofer, _ = Usuario.objects.get_or_create(
            rut="33333333-3",
            nombre_completo="Pedro Chofer",
            email="pedro@demo.cl",
            rol="CHOFER",
            hash_contrasena="1234"
        )

        # Vehículos
        vehiculo, _ = Vehiculo.objects.get_or_create(
            patente="TPKP25",
            marca="Toyota",
            modelo="RAV4 2.0 4x2",
            año_modelo=2024,
            conductor_actual_id=chofer.id
        )

        # Orden de trabajo
        OrdenTrabajo.objects.get_or_create(
            numero_ot="OT-0001",
            vehiculo_id=vehiculo.id,
            taller_id=taller.id,
            usuario_solicitante_id=admin.id,
            mecanico_asignado_id=mecanico.id,
            descripcion_problema="Revisión general preventiva."
        )

        self.stdout.write(self.style.SUCCESS("Datos de prueba cargados correctamente ✔"))
