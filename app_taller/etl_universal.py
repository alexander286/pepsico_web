# app_taller/etl_universal.py

import os
import csv
import io

import openpyxl
from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect

from .etl_utils import (
    normalizar_rut,
    normalizar_nombre,
    normalizar_email,
    normalizar_patente,
    validar_patente,
)

from .models import Usuario, Taller, Vehiculo, Repuesto


# ==========================
# HELPERS GENERALES
# ==========================

def detectar_tipo_archivo(nombre: str) -> str:
    nombre = (nombre or "").lower()

    if nombre.endswith(".xlsx") or nombre.endswith(".xls"):
        return "excel"
    if nombre.endswith(".csv"):
        return "csv"
    if nombre.endswith(".txt"):
        return "texto"
    if nombre.endswith(".pdf"):
        return "pdf"
    if nombre.endswith(".sql"):
        return "sql"

    return "desconocido"


def leer_excel(uploaded_file):
    """
    Lee la primera hoja de un Excel y devuelve una lista de filas (listas de celdas).
    Limpia filas totalmente vacías.
    """
    wb = openpyxl.load_workbook(uploaded_file, data_only=True)
    ws = wb.active
    data = []

    for row in ws.iter_rows(values_only=True):
        # row es una tupla, la convertimos y limpiamos
        if any(row):
            data.append([str(x).strip() if x is not None else "" for x in row])

    return data


def leer_csv(uploaded_file):
    """
    Lee un CSV en UTF-8 (ignora caracteres raros).
    """
    text = uploaded_file.read().decode("utf-8", errors="ignore")
    reader = csv.reader(io.StringIO(text))
    data = []
    for row in reader:
        if any(row):
            data.append([c.strip() for c in row])
    return data


def _norm(s: str) -> str:
    return (s or "").strip().lower()


# ==========================
# DETECCIÓN DE TIPO DE TABLA
# ==========================

def detectar_tabla_por_columnas(headers):
    """
    Según las columnas del archivo, decide qué entidad es:
    - usuarios
    - vehiculos
    - repuestos
    - desconocido
    """
    # DEBUG: imprime las cabeceras en la consola
    print("DEBUG ETL - HEADERS:", headers)

    cols = [_norm(h) for h in headers]

    # usuarios: rut + email
    if any("rut" in c for c in cols) and any("email" in c or "correo" in c for c in cols):
        return "usuarios"

    # vehículos: patente + marca o modelo
    if any("patente" in c for c in cols) and (
        any("marca" in c for c in cols) or any("modelo" in c for c in cols)
    ):
        return "vehiculos"

    # repuestos: codigo/sku + nombre
    if (any("codigo" in c for c in cols) or any("sku" in c for c in cols)) and any(
        "nombre" in c for c in cols
    ):
        return "repuestos"

    return "desconocido"


# ==========================
# PROCESADORES POR ENTIDAD
# ==========================

def procesar_usuarios(headers, rows):
    """
    UPSERT de usuarios:
    - Clave: email
    - No borra nada.
    - Actualiza si ya existe, crea si no.
    """
    errores = []
    ok = 0

    idx = { _norm(h): i for i, h in enumerate(headers) }

    def col(*nombres_posibles):
        for n in nombres_posibles:
            for k, i in idx.items():
                if n in k:
                    return i
        return None

    i_rut = col("rut")
    i_nombre = col("nombre completo", "nombre", "nombre y apellido")
    i_email = col("email", "correo")
    i_rol = col("rol")
    i_taller = col("taller")
    i_tel = col("telefono", "teléfono")
    i_activo = col("activo", "estado", "vigente")

    for row_num, row in enumerate(rows, start=2):  # fila 2 en adelante (1 = headers)
        try:
            rut = normalizar_rut(row[i_rut]) if i_rut is not None and row[i_rut] else ""
            nombre = normalizar_nombre(row[i_nombre]) if i_nombre is not None and row[i_nombre] else ""
            email_raw = row[i_email] if i_email is not None and row[i_email] else ""
            email = normalizar_email(email_raw)

            if not email:
                errores.append(f"Fila {row_num}: sin email, no se puede identificar usuario.")
                continue

            rol = (row[i_rol] or "").strip().upper() if i_rol is not None and row[i_rol] else ""
            taller_nombre = (row[i_taller] or "").strip() if i_taller is not None and row[i_taller] else ""
            telefono = (row[i_tel] or "").strip() if i_tel is not None and row[i_tel] else ""

            activo = True
            if i_activo is not None and row[i_activo]:
                val = str(row[i_activo]).strip().upper()
                if val in {"NO", "N", "0", "FALSE"}:
                    activo = False

            taller_obj = None
            if taller_nombre:
                taller_obj = Taller.objects.filter(nombre__iexact=taller_nombre).first()

            usuario, created = Usuario.objects.get_or_create(
                email=email,
                defaults={
                    "rut": rut,
                    "nombre_completo": nombre or email,
                    "rol": rol or "SIN_ROL",
                    "telefono": telefono,
                    "activo": activo,
                },
            )

            if not created:
                # actualizar campos si vienen
                if rut:
                    usuario.rut = rut
                if nombre:
                    usuario.nombre_completo = nombre
                if rol:
                    usuario.rol = rol
                if telefono:
                    usuario.telefono = telefono
                usuario.activo = activo

            if taller_obj and hasattr(usuario, "taller"):
                usuario.taller = taller_obj

            usuario.save()
            ok += 1

        except Exception as e:
            errores.append(f"Fila {row_num}: error inesperado → {e}")

    return ok, errores


def procesar_vehiculos(headers, rows):
    """
    UPSERT de vehículos:
    - Clave: patente
    """
    errores = []
    ok = 0

    idx = { _norm(h): i for i, h in enumerate(headers) }

    def col(*nombres_posibles):
        for n in nombres_posibles:
            for k, i in idx.items():
                if n in k:
                    return i
        return None

    i_pat = col("patente")
    i_marca = col("marca")
    i_modelo = col("modelo")
    i_anio = col("año modelo", "ano modelo", "año", "ano")
    i_estado = col("estado")

    if i_pat is None:
        return 0, ["No se encontró columna de 'Patente' en el archivo."]

    for row_num, row in enumerate(rows, start=2):
        try:
            patente_raw = row[i_pat] if i_pat is not None and row[i_pat] else ""
            patente = normalizar_patente(patente_raw)

            if not patente:
                errores.append(f"Fila {row_num}: patente vacía.")
                continue

            if not validar_patente(patente):
                errores.append(f"Fila {row_num}: patente inválida → {patente_raw}")
                continue

            marca = (row[i_marca] or "").strip() if i_marca is not None and row[i_marca] else ""
            modelo = (row[i_modelo] or "").strip() if i_modelo is not None and row[i_modelo] else ""
            anio = None
            if i_anio is not None and row[i_anio]:
                try:
                    anio = int(str(row[i_anio]).strip())
                except ValueError:
                    errores.append(f"Fila {row_num}: año modelo inválido → {row[i_anio]}")
            estado = (row[i_estado] or "").strip().upper() if i_estado is not None and row[i_estado] else ""

            veh, created = Vehiculo.objects.get_or_create(
                patente=patente,
                defaults={
                    "marca": marca,
                    "modelo": modelo,
                    "año_modelo": anio,
                    "estado": estado,
                },
            )

            if not created:
                if marca:
                    veh.marca = marca
                if modelo:
                    veh.modelo = modelo
                if anio is not None:
                    veh.año_modelo = anio
                if estado:
                    veh.estado = estado
                veh.save()

            ok += 1

        except Exception as e:
            errores.append(f"Fila {row_num}: error inesperado → {e}")

    return ok, errores


def procesar_repuestos(headers, rows):
    """
    UPSERT de repuestos:
    - Clave: codigo o sku
    """
    errores = []
    ok = 0

    idx = { _norm(h): i for i, h in enumerate(headers) }

    def col(*nombres_posibles):
        for n in nombres_posibles:
            for k, i in idx.items():
                if n in k:
                    return i
        return None

    i_codigo = col("codigo", "código", "sku")
    i_nombre = col("nombre")
    i_categoria = col("categoria", "categoría", "tipo")
    i_precio = col("precio costo", "precio_costo", "precio")
    i_unidad = col("unidad", "unidad de medida", "unidad_medida")
    i_stock = col("stock", "cantidad", "cantidad disponible")
    i_stock_min = col("stock minimo", "stock mínimo", "stock_min")
    i_activo = col("activo", "vigente")

    if i_codigo is None:
        return 0, ["No se encontró columna de 'Código/SKU' en el archivo de repuestos."]

    for row_num, row in enumerate(rows, start=2):
        try:
            codigo = (row[i_codigo] or "").strip() if row[i_codigo] else ""
            if not codigo:
                errores.append(f"Fila {row_num}: sin código/SKU.")
                continue

            nombre = (row[i_nombre] or "").strip() if i_nombre is not None and row[i_nombre] else codigo
            categoria = (row[i_categoria] or "").strip() if i_categoria is not None and row[i_categoria] else ""
            precio = None
            if i_precio is not None and row[i_precio]:
                try:
                    precio = float(str(row[i_precio]).replace(",", "."))
                except ValueError:
                    errores.append(f"Fila {row_num}: precio inválido → {row[i_precio]}")

            unidad = (row[i_unidad] or "").strip() if i_unidad is not None and row[i_unidad] else ""
            stock = None
            if i_stock is not None and row[i_stock]:
                try:
                    stock = int(float(str(row[i_stock]).replace(",", ".")))
                except ValueError:
                    errores.append(f"Fila {row_num}: stock inválido → {row[i_stock]}")

            stock_min = None
            if i_stock_min is not None and row[i_stock_min]:
                try:
                    stock_min = int(float(str(row[i_stock_min]).replace(",", ".")))
                except ValueError:
                    errores.append(f"Fila {row_num}: stock mínimo inválido → {row[i_stock_min]}")

            activo = True
            if i_activo is not None and row[i_activo]:
                v = str(row[i_activo]).strip().upper()
                if v in {"NO", "N", "0", "FALSE"}:
                    activo = False

            rep, created = Repuesto.objects.get_or_create(
                codigo=codigo,
                defaults={
                    "nombre": nombre,
                    "categoria": categoria,
                    "precio_costo": precio,
                    "unidad_medida": unidad,
                    "stock": stock if stock is not None else 0,
                    "stock_minimo": stock_min if stock_min is not None else 0,
                    "activo": activo,
                },
            )

            if not created:
                if nombre:
                    rep.nombre = nombre
                if categoria:
                    rep.categoria = categoria
                if precio is not None:
                    rep.precio_costo = precio
                if unidad:
                    rep.unidad_medida = unidad
                if stock is not None:
                    rep.stock = stock
                if stock_min is not None:
                    rep.stock_minimo = stock_min
                rep.activo = activo
                rep.save()

            ok += 1

        except Exception as e:
            errores.append(f"Fila {row_num}: error inesperado → {e}")

    return ok, errores


# ==========================
# ORQUESTADOR PRINCIPAL
# ==========================

def procesar_datos(data):
    """
    Orquesta el ETL:
    - Detecta la entidad por encabezados.
    - Llama al procesador correspondiente.
    """
    if not data or len(data) < 2:
        return 0, ["El archivo no contiene datos suficientes (mínimo encabezado + 1 fila)."]

    headers = data[0]
    rows = data[1:]

    tipo_tabla = detectar_tabla_por_columnas(headers)

    if tipo_tabla == "usuarios":
        return procesar_usuarios(headers, rows)
    elif tipo_tabla == "vehiculos":
        return procesar_vehiculos(headers, rows)
    elif tipo_tabla == "repuestos":
        return procesar_repuestos(headers, rows)
    else:
        return 0, [
            "No se reconoció el tipo de datos por las columnas.",
            f"Encabezados detectados: {headers}",
        ]


# ==========================
# VISTA/LÓGICA INVOCADA DESDE PANEL ADMIN
# ==========================
# app_taller/etl_universal.py
from django.shortcuts import redirect
from django.contrib import messages
from django.db import transaction

# ... (resto de imports y funciones arriba)


def importar_archivo_universal(request):
    """
    Esta función se llama desde el panel de admin_excel_panel.
    Form:
      <form method="post" enctype="multipart/form-data" action="{% url 'admin_etl_universal' %}">
    """
    if request.method == "POST":
        uploaded_file = request.FILES.get("archivo")

        if not uploaded_file:
            messages.error(request, "No se recibió ningún archivo para procesar.")
            return redirect("panel_admin_excel")  # 👈 mismo panel

        filename = uploaded_file.name
        tipo_archivo = detectar_tipo_archivo(filename)

        ok = 0
        errores = []

        try:
            # 1) LEER DATOS SEGÚN EL TIPO DE ARCHIVO
            if tipo_archivo == "excel":
                data = leer_excel(uploaded_file)
            elif tipo_archivo == "csv":
                data = leer_csv(uploaded_file)
            else:
                # otros tipos solamente se informan, no se procesan
                mensajes = {
                    "texto": "Archivos TXT se aceptan pero no se cargan a BD (no tabulares).",
                    "pdf": "PDF recibido. No se procesan tablas automáticamente en esta versión.",
                    "sql": "Archivo SQL recibido. Requiere revisión manual (no ejecutado por seguridad).",
                }
                msg = mensajes.get(tipo_archivo, f"Formato no soportado: {filename}")
                messages.warning(request, msg)
                return redirect("panel_admin_excel")

            # 2) DEBUG: ver qué tipo de tabla detectamos por encabezados
            headers = data[0] if data else []
            tipo_tabla = detectar_tabla_por_columnas(headers)
            messages.info(request, f"Tipo archivo: {tipo_archivo} | Tipo tabla detectado: {tipo_tabla}")

            # 3) *** PRUEBA RÁPIDA: FORZAR PROCESADOR ***
            # ⚠️ Deja SOLO UNA de estas líneas activa según lo que estés probando.
            #
            #   - Si estás probando un Excel de usuarios, deja procesar_usuarios
            #   - Si estás probando un Excel de vehículos, deja procesar_vehiculos
            #   - Si estás probando un Excel de repuestos, deja procesar_repuestos

            with transaction.atomic():
                # --- DESCOMENTA SOLO UNA SEGÚN EL ARCHIVO QUE SUBAS ---
                ok, errores = procesar_usuarios(headers, data[1:])
                # ok, errores = procesar_vehiculos(headers, data[1:])
                # ok, errores = procesar_repuestos(headers, data[1:])

                # 🔁 Versión automática (cuando ya veas que funciona la de arriba)
                #ok, errores = procesar_datos(data)

        except Exception as e:
            errores.append(f"Error global procesando el archivo: {e}")

        if ok > 0:
            messages.success(request, f"Archivo '{filename}' procesado correctamente. Registros OK: {ok}.")
        else:
            messages.warning(request, f"Archivo '{filename}' procesado sin registros cargados.")

        for err in errores:
            messages.warning(request, err)

        return redirect("panel_admin_excel")

    # Si alguien entra por GET directo, lo mandamos al panel de excel
    return redirect("panel_admin_excel")
