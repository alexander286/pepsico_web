# app_taller/services/inventario_client.py
import json
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from django.conf import settings

try:
    import requests
except Exception:
    requests = None  # por si no está instalado

@dataclass
class Item:
    code: str
    name: str
    qty: float

class InventarioClient:
    def __init__(self):
        self.enabled = bool(getattr(settings, "INV_API_ENABLED", False))
        self.base = getattr(settings, "INV_API_BASE", "").rstrip("/")
        self.timeout = int(getattr(settings, "INV_API_TIMEOUT", 2))
        self.retries = int(getattr(settings, "INV_API_RETRIES", 0))
        # no prepares session si está deshabilitado o no hay requests
        self.session = requests.Session() if (self.enabled and requests) else None

    def _should_call(self) -> bool:
        return bool(self.enabled and self.session and self.base)

    # Ejemplo: confirmar entrega de un ítem
    def confirmar_entrega(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        payload: {"ot": "...", "item_code": "...", "item_name": "...", "quantity": 1, ...}
        """
        if not self._should_call():
            # Modo “stub”: simula OK inmediato para no trabar el flujo
            return {"status": "stubbed", "ok": True}

        url = f"{self.base}/entregas/confirmar"
        # un único intento aquí; los reintentos los maneja el sync offline
        r = self.session.post(url, json=payload, timeout=self.timeout)
        r.raise_for_status()
        return r.json()
