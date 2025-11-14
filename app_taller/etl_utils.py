import re

# -----------------------------------------
# NORMALIZACIONES BÁSICAS (ETL)
# -----------------------------------------

def normalizar_patente(raw):
    """
    E → T → L
    Limpia y normaliza patentes chilenas: ABCD12 / AB1234 / AB12CD
    """
    if not raw:
        return ""
    raw = raw.upper().replace(" ", "").strip()
    return raw


def normalizar_rut(raw):
    """
    Limpia puntos, normaliza guion y retorna RUT estándar: 12345678-K
    """
    if not raw:
        return ""

    raw = raw.upper().strip()
    raw = raw.replace(".", "").replace(" ", "")

    if "-" not in raw:
        return raw[:-1] + "-" + raw[-1]

    return raw


def normalizar_email(raw):
    """
    Emails van siempre en minúsculas y sin espacios.
    """
    if not raw:
        return ""
    return raw.strip().lower()


def normalizar_nombre(raw):
    """
    Nombres en formato título (primera letra mayúscula)
    """
    if not raw:
        return ""
    return raw.strip().title()


# -----------------------------------------
# VALIDACIONES (ETL)
# -----------------------------------------

def validar_patente(raw):
    """
    Retorna True si una patente chilena es válida.
    """
    if not raw:
        return False

    raw = normalizar_patente(raw)

    patrones = [
        r"^[A-Z]{4}[0-9]{2}$",   # ABCD12
        r"^[A-Z]{2}[0-9]{4}$",   # AB1234
        r"^[A-Z]{2}[0-9]{2}[A-Z]{2}$",  # AB12CD
    ]

    return any(re.match(p, raw) for p in patrones)


def validar_rut(raw):
    """
    Valida que tenga formato básico con dígito verificador.
    No valida algoritmo Módulo 11 (opcional)
    """
    if not raw:
        return False

    return bool(re.match(r"^[0-9]{1,8}-[0-9K]$", normalizar_rut(raw)))
