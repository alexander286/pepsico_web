# app_taller/etl_universal.py
import csv
import io
import json
from pathlib import Path
from typing import Tuple, List

import openpyxl
import PyPDF2

from django.db import transaction, IntegrityError
from django.utils import timezone

from .models import Usuario, Vehiculo, OrdenTrabajo, Repuesto
from .etl_utils import (
    normalizar_patente,
    normalizar_email,
    normalizar_rut,
    normalizar_nombre,
)


# ======================================================
# 1) DETECCIÓN DE FORMATO
# ======================================================
def detectar_tipo_archivo(filename: str) -> str:
    ext = filename.lower().split(".")[-1]

    if ext in ("xlsx", "xls"):
        return "excel"
    elif ext in ("csv",):
        return "csv"
    elif ext in ("txt", "log"):
        return "texto"
    elif ext in ("sql",):
        return "sql"
    elif ext in ("pdf",):
        return "pdf"
    else:
        return "desconocido"


# ======================================================
# 2) LECTURA SEGÚN TIPO
# ======================================================
def leer_excel(file) -> List[dict]:
    wb = openpyxl.load_workbook(file, data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    headers = [str(h).strip() for h in rows[0]]

    data = []
    for row in rows[1:]:
        data.append({headers[i]: row[i] for i in range(len(headers))})
    return data


def leer_csv(file) -> List[dict]:
    text = file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


def leer_txt(file) -> List[str]:
    return file.read().decode("utf-8").splitlines()


def leer_pdf(file) -> List[str]:
    pdf = PyPDF2.PdfReader(file)
    lines = []
    for page in pdf.pages:
        lines.extend(page.extract_text().splitlines())
    return lines


def leer_sql(file) -> str:
    return file.read().decode("utf-8")


# ======================================================
# 3) PROCESAMIENTO DE CONTENIDO → MODELO (ETL)
# ======================================================
def procesar_datos(data: List[dict]) -> Tuple[int, List[str]]:
    """
    Recibe una lista de filas (dict) y trata de clasificar automáticamente
    si son Usuarios, Vehículos, Repuestos u OTs.
    """
    errores = []
    ok = 0

    for idx, row in enumerate(data, start=1):
        try:
            # ===========================================
            # 1) ¿Es un Usuario?
            # ===========================================
            if "email" in row or "correo" in row:
                email = normalizar_email(row.get("email") or row.get("correo"))
                if not email:
                    continue

                usuario, _ = Usuario.objects.update_or_create(
                    email=email,
                    defaults={
                        "nombre_completo": normalizar_nombre(row.get("nombre") or ""),
                        "rut": normalizar_rut(row.get("rut") or ""),
                        "rol": (row.get("rol") or "USUARIO").upper(),
                        "telefono": row.get("telefono") or "",
                        "activo": True,
                    },
                )
                ok += 1
                continue

            # ===========================================
            # 2) ¿Es un Vehículo?
            # ===========================================
            if "patente" in row:
                pat = normalizar_patente(row.get("patente"))
                if not pat:
                    continue

                Vehiculo.objects.update_or_create(
                    patente=pat,
                    defaults={
                        "marca": row.get("marca") or "",
                        "modelo": row.get("modelo") or "",
                        "año_modelo": row.get("año") or row.get("anio") or None,
                        "estado": (row.get("estado") or "").upper(),
                    },
                )
                ok += 1
                continue

            # ===========================================
            # 3) ¿Es un Repuesto?
            # ===========================================
            if "repuesto" in row or "sku" in row:
                sku = (row.get("sku") or row.get("codigo") or "").upper()
                if not sku:
                    continue

                Repuesto.objects.update_or_create(
                    sku=sku,
                    defaults={
                        "nombre": row.get("nombre") or "",
                        "precio_costo": row.get("precio") or 0,
                        "unidad": row.get("unidad") or "UN",
                        "activo": True,
                    },
                )
                ok += 1
                continue

            # ===========================================
            # 4) ¿Es una OT?
            # ===========================================
            if "n_ot" in row or "numero_ot" in row:
                OrdenTrabajo.objects.update_or_create(
                    numero_ot=row.get("numero_ot") or row.get("n_ot"),
                    defaults={
                        "estado": row.get("estado") or "PENDIENTE",
                        "prioridad": row.get("prioridad") or "NORMAL",
                    },
                )
                ok += 1
                continue

        except Exception as e:
            errores.append(f"Fila {idx}: {e}")

    return ok, errores


# ======================================================
# 4) FUNCIÓN PRINCIPAL: IMPORTAR UNIVERSAL
# ======================================================
def importar_archivo_universal(uploaded_file):
    tipo = detectar_tipo_archivo(uploaded_file.name)

    if tipo == "excel":
        data = leer_excel(uploaded_file)
        return procesar_datos(data)

    elif tipo == "csv":
        data = leer_csv(uploaded_file)
        return procesar_datos(data)

    elif tipo == "texto":
        # no se guardan en BD, solo procesables
        return 0, ["TXT importado (sin tratamiento de BD)."]

    elif tipo == "pdf":
        return 0, ["PDF importado (sin estructura tabular)."]

    elif tipo == "sql":
        return 0, ["Archivo SQL importado (requiere evaluación manual)."]

    else:
        return 0, [f"Formato no soportado: {uploaded_file.name}"]
