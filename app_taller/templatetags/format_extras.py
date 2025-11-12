# app_taller/templatetags/format_extras.py
from decimal import Decimal
from django import template

register = template.Library()

def _fmt_chile(n, decimals=0):
    q = Decimal(n or 0)
    txt = f"{q:,.{decimals}f}"            # 1,234,567.89
    txt = txt.replace(",", "X").replace(".", ",").replace("X", ".")  # 1.234.567,89
    return f"${txt}"

@register.filter(name="clp")
def clp(value):
    """$1.234.567 (0 decimales)"""
    return _fmt_chile(value, 0)

@register.filter(name="clp2")
def clp2(value):
    """$1.234.567,89 (2 decimales)"""
    return _fmt_chile(value, 2)

@register.filter(name="mul")
def mul(a, b):
    """Multiplica dos números (Decimal-safe)"""
    try:
        return Decimal(a or 0) * Decimal(b or 0)
    except Exception:
        return Decimal(0)
