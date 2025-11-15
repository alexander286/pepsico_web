# app_taller/excel_utils.py
import io
from typing import List, Tuple
from django.utils import timezone 
from django.http import HttpResponse
from openpyxl import Workbook, load_workbook
from .etl_utils import normalizar_rut, normalizar_nombre, normalizar_email

from .models import Usuario, Vehiculo, Taller, OrdenTrabajo,SolicitudRepuesto, Repuesto,MovimientoRepuesto 

from openpyxl import Workbook
from django.http import HttpResponse
from io import BytesIO
from app_taller.models import Usuario
# =======================
# EXPORTAR A EXCEL
# =======================
def exportar_usuarios_xlsx():
    wb = Workbook()
    ws = wb.active
    ws.title = "Usuarios"

    # Encabezados
    ws.append(["RUT", "Nombre", "Email", "Rol", "Teléfono", "Activo"])

    for u in Usuario.objects.all():
        ws.append([u.rut, u.nombre_completo, u.email, u.rol, u.telefono, "Sí" if u.activo else "No"])

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(
        output,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename=usuarios.xlsx'
    return response

    # Guardar en memoria
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    resp = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
def exportar_ots_xlsx() -> HttpResponse:
    wb = Workbook()
    ws = wb.active
    ws.title = "OrdenesTrabajo"

    headers = [
        "N° OT",
        "Patente",
        "Estado",
        "Prioridad",
        "Mecánico asignado",
        "Taller",
        "Fecha apertura",
        "Total repuestos",
        "Total costo repuestos",
    ]
    ws.append(headers)

    qs = (
        OrdenTrabajo.objects
        .select_related("vehiculo", "mecanico_asignado", "taller")
        .all()
        .order_by("numero_ot")
    )

    for ot in qs:
        mecanico_nombre = ""
        if getattr(ot, "mecanico_asignado", None):
            mecanico_nombre = getattr(ot.mecanico_asignado, "nombre_completo", "") or ""

        taller_nombre = ""
        if getattr(ot, "taller", None):
            taller_nombre = getattr(ot.taller, "nombre", "") or ""

        total_repuestos = getattr(ot, "total_repuestos", 0) or 0
        total_costo_repuestos = getattr(ot, "total_costo_repuestos", 0) or 0

        ws.append([
            ot.numero_ot,
            getattr(ot.vehiculo, "patente", "") if ot.vehiculo_id else "",
            getattr(ot, "get_estado_display", lambda: ot.estado)(),
            getattr(ot, "get_prioridad_display", lambda: ot.prioridad)(),
            mecanico_nombre,
            taller_nombre,
            ot.fecha_apertura.strftime("%d-%m-%Y %H:%M") if ot.fecha_apertura else "",
            total_repuestos,
            float(total_costo_repuestos),
        ])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    resp = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = 'attachment; filename="ordenes_trabajo.xlsx"'
    return resp


def exportar_solicitudes_repuesto_xlsx() -> HttpResponse:
    wb = Workbook()
    ws = wb.active
    ws.title = "SolicitudesRepuesto"

    headers = [
        "ID solicitud",
        "N° OT",
        "Repuesto",
        "Cantidad",
        "Urgente",
        "Estado",
        "N° OC",
        "Proveedor",
        "Fecha entrega estimada",
        "Creado por",
        "Fecha creación",
    ]
    ws.append(headers)

    qs = (
        SolicitudRepuesto.objects
        .select_related("orden_trabajo", "repuesto", "creado_por")
        .all()
        .order_by("-fecha_creacion")
    )

    for s in qs:
        ot_num = s.orden_trabajo.numero_ot if s.orden_trabajo_id else ""
        rep_name = ""
        if s.repuesto_id:
            rep_name = getattr(s.repuesto, "nombre", str(s.repuesto)) or str(s.repuesto)

        creador = ""
        if s.creado_por_id:
            creador = getattr(s.creado_por, "nombre_completo", "") or s.creado_por.email

        if hasattr(s, "get_estado_display"):
            estado = s.get_estado_display()
        else:
            estado = s.estado

        ws.append([
            s.id,
            ot_num,
            rep_name,
            getattr(s, "cantidad_solicitada", getattr(s, "cantidad", 0)) or 0,
            "SI" if s.urgente else "NO",
            estado,
            s.numero_oc or "",
            s.nombre_proveedor or "",
            s.fecha_entrega_estimada.strftime("%d-%m-%Y") if s.fecha_entrega_estimada else "",
            creador,
            s.fecha_creacion.strftime("%d-%m-%Y %H:%M") if s.fecha_creacion else "",
        ])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    resp = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = 'attachment; filename="solicitudes_repuesto.xlsx"'
    return resp

    



def exportar_vehiculos_xlsx() -> HttpResponse:
    wb = Workbook()
    ws = wb.active
    ws.title = "Vehículos"

    headers = ["Patente", "Marca", "Modelo", "Año modelo", "Estado"]
    ws.append(headers)

    from .models import Vehiculo  # importar aquí para evitar ciclos

    for v in Vehiculo.objects.all().order_by("patente"):
        ws.append([
            v.patente or "",
            getattr(v, "marca", "") or "",
            getattr(v, "modelo", "") or "",
            getattr(v, "año_modelo", "") or getattr(v, "anio_modelo", "") or "",
            getattr(v, "estado", "") or "",
        ])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    resp = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = 'attachment; filename="vehiculos.xlsx"'
    return resp


# =======================
# IMPORTAR DESDE EXCEL
# =======================

import openpyxl

def importar_usuarios_xlsx(file):
    errores = []
    wb = openpyxl.load_workbook(file)
    ws = wb.active

    headers = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]

    for i, row_cells in enumerate(ws.iter_rows(min_row=2), start=2):
        row = {headers[j]: cell.value for j, cell in enumerate(row_cells) if j < len(headers)}

        try:
            rut = normalizar_rut(row.get("RUT"))
            email = (row.get("Email") or "").strip().lower()
            nombre = row.get("Nombre completo") or ""
            rol = row.get("Rol") or ""
            telefono = row.get("Teléfono") or ""
            activo = str(row.get("Activo") or "").strip().lower() == "sí"

            if not rut or not email:
                errores.append(f"Fila {i}: RUT o Email faltante")
                continue

            usuario, created = Usuario.objects.update_or_create(
                rut=rut,
                defaults={
                    "email": email,
                    "nombre_completo": nombre,
                    "rol": rol,
                    "telefono": telefono,
                    "activo": activo,
                }
            )
        except Exception as e:
            errores.append(f"Fila {i}: {str(e)}")

    return True, errores


from .etl_utils import normalizar_patente

def importar_vehiculos_xlsx(uploaded_file) -> Tuple[int, List[str]]:
    """
    Similar a usuarios, pero para vehículos.
    Encabezados esperados: Patente, Marca, Modelo, Año modelo, Estado
    """
    from .models import Vehiculo

    wb = load_workbook(uploaded_file, data_only=True)
    ws = wb.active

    errores: List[str] = []
    ok = 0

    first = True
    for row_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
        if first:
            first = False
            continue

        patente, marca, modelo, anio, estado = (row + (None,) * 5)[:5]

        if not patente:
            continue

        pat = normalizar_patente(row["Patente"])

        if not validar_patente(pat):
            errores.append(f"Patente inválida: {row['Patente']}")
            continue


        veh, created = Vehiculo.objects.get_or_create(
            patente=patente,
            defaults={
                "marca": (marca or "").strip() if marca else "",
                "modelo": (modelo or "").strip() if modelo else "",
                "año_modelo": anio or None,
                "estado": (estado or "").strip().upper() if estado else "",
            },
        )

        if not created:
            if marca:
                veh.marca = str(marca).strip()
            if modelo:
                veh.modelo = str(modelo).strip()
            if anio:
                veh.año_modelo = anio
            if estado:
                veh.estado = str(estado).strip().upper()
            veh.save()

        ok += 1

    return ok, errores



def exportar_ots_xlsx():
    wb = Workbook()
    ws = wb.active
    ws.title = "OTs"

    # Encabezados
    headers = [
        "Número OT",
        "Patente",
        "Taller",
        "Estado",
        "Prioridad",
        "Mecánico asignado",
        "Fecha apertura",
        "Total repuestos",
        "Costo total repuestos",
    ]
    ws.append(headers)

    qs = (
        OrdenTrabajo.objects
        .select_related("vehiculo", "taller", "mecanico_asignado")
        .all()
        .order_by("-fecha_apertura")
    )

    for ot in qs:
        veh = getattr(ot, "vehiculo", None)
        mec = getattr(ot, "mecanico_asignado", None)
        tall = getattr(ot, "taller", None)

        patente = getattr(veh, "patente", "") if veh else ""
        taller_nombre = getattr(tall, "nombre", "") if tall else ""
        mecanico_nombre = getattr(mec, "nombre_completo", "") if mec else ""

        total_repuestos = getattr(ot, "total_repuestos", None)
        costo_total = getattr(ot, "total_costo_repuestos", None)

        # 🔹 Arreglar datetime con timezone → datetime “naive”
        fecha_ap = getattr(ot, "fecha_apertura", None)
        if fecha_ap is not None and timezone.is_aware(fecha_ap):
            fecha_ap = timezone.make_naive(fecha_ap)

        ws.append([
            ot.numero_ot,
            patente,
            taller_nombre,
            ot.estado,
            ot.prioridad,
            mecanico_nombre,
            fecha_ap,  #
            total_repuestos if total_repuestos is not None else "",
            float(costo_total) if costo_total is not None else "",
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="ordenes_trabajo.xlsx"'
    wb.save(response)
    return response

def exportar_solicitudes_xlsx():
    wb = Workbook()
    ws = wb.active
    ws.title = "Solicitudes Repuestos"

    headers = [
        "ID",
        "N° OT",
        "Patente",
        "Repuesto",
        "Cantidad solicitada",
        "Urgente",
        "Estado",
        "N° OC",
        "Proveedor",
        "Fecha entrega estimada",
        "Creado por",
        "Fecha creación",
        "Fecha actualización",
    ]
    ws.append(headers)

    qs = (
        SolicitudRepuesto.objects
        .select_related("orden_trabajo", "orden_trabajo__vehiculo", "repuesto", "creado_por")
        .all()
        .order_by("-fecha_creacion")
    )

    for s in qs:
        ot = s.orden_trabajo
        veh = getattr(ot, "vehiculo", None)

        ws.append([
            s.id,
            getattr(ot, "numero_ot", "") if ot else "",
            getattr(veh, "patente", "") if veh else "",
            str(s.repuesto),
            getattr(s, "cantidad_solicitada", None),
            "Sí" if s.urgente else "No",
            s.estado,
            s.numero_oc or "",
            s.nombre_proveedor or "",
            _safe_dt(s.fecha_entrega_estimada),
            getattr(s.creado_por, "nombre_completo", "") if s.creado_por_id else "",
            _safe_dt(s.fecha_creacion),
            _safe_dt(s.fecha_actualizacion),
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    filename = f"solicitudes_repuestos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response

def exportar_movimientos_xlsx():
    wb = Workbook()
    ws = wb.active
    ws.title = "Movimientos Repuestos"

    headers = [
        "ID",
        "Fecha movimiento",
        "Taller",
        "N° OT",
        "Patente",
        "Repuesto",
        "Tipo movimiento",
        "Cantidad",
        "Costo unitario",
        "Subtotal",
        "Motivo",
        "Movido por",
    ]
    ws.append(headers)

    qs = (
        MovimientoRepuesto.objects
        .select_related("taller", "orden_trabajo", "orden_trabajo__vehiculo", "repuesto", "movido_por")
        .all()
        .order_by("-fecha_movimiento")
    )

    for m in qs:
        ot = m.orden_trabajo
        veh = getattr(ot, "vehiculo", None)
        subtotal = None
        if m.costo_unitario is not None and m.cantidad is not None:
            subtotal = m.costo_unitario * m.cantidad

        ws.append([
            m.id,
            _safe_dt(m.fecha_movimiento),
            getattr(m.taller, "nombre", "") if m.taller_id else "",
            getattr(ot, "numero_ot", "") if ot else "",
            getattr(veh, "patente", "") if veh else "",
            str(m.repuesto),
            m.tipo_movimiento,
            m.cantidad,
            m.costo_unitario,
            subtotal,
            m.motivo or "",
            getattr(m.movido_por, "nombre_completo", "") if m.movido_por_id else "",
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    filename = f"movimientos_repuestos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response








def _safe_dt(dt):
    """Convierte datetimes con tz en naive para Excel."""
    if not dt:
        return None
    if hasattr(dt, "tzinfo") and dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


from datetime import datetime

def exportar_repuestos_xlsx():
    wb = Workbook()
    ws = wb.active
    ws.title = "Repuestos"

    headers = [
        "ID",
        "Código",
        "Nombre",
        "Categoría",
        "Precio costo",
        "Unidad",
        "Stock",
        "Stock mínimo",
        "Activo",
    ]
    ws.append(headers)

    qs = Repuesto.objects.all().order_by("id")

    for r in qs:
        codigo = getattr(r, "codigo", None) or getattr(r, "sku", None) or ""
        nombre = getattr(r, "nombre", str(r))
        categoria = getattr(r, "categoria", "") or getattr(r, "tipo", "")
        precio = getattr(r, "precio_costo", None) or getattr(r, "precio", None)
        unidad = getattr(r, "unidad_medida", "") or getattr(r, "unidad", "")
        stock = getattr(r, "stock", None) or getattr(r, "cantidad_disponible", None)
        stock_min = getattr(r, "stock_minimo", None) or getattr(r, "stock_min", None)
        activo = getattr(r, "activo", True)

        ws.append([
            r.id,
            codigo,
            nombre,
            categoria,
            precio,
            unidad,
            stock,
            stock_min,
            "Sí" if activo else "No",
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    filename = f"repuestos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response




