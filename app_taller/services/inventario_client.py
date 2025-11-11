# app_taller/services/inventario_client.py
from dataclasses import dataclass
from typing import List, Dict, Any
import time, hashlib, hmac, json
from django.conf import settings

@dataclass
class Item:
    sku: str
    cantidad: int

class InventarioClient:
    def __init__(self):
        self.base = settings.INV_API_BASE
        self.token = settings.INV_API_TOKEN
        self.mode = settings.INV_API_MODE.upper()
        self.timeout = settings.INV_API_TIMEOUT
        self.retries = settings.INV_API_RETRIES

    def _idempotency(self, ot: str, items: List[Item]) -> str:
        base = f"{ot}|{json.dumps([i.__dict__ for i in items], sort_keys=True)}"
        return hashlib.sha256(base.encode()).hexdigest()

    # --- MOCK responses ---
    def _mock_ok(self, **kw) -> Dict[str, Any]:
        return {"ok": True, "mov_id": "MOCK-MOV-{}".format(int(time.time())), "extra": kw}

    def check_stock(self, sku: str) -> Dict[str, Any]:
        if self.mode == "OFF":  # “caída”
            return {"ok": False, "error": "API inventario OFF"}
        if self.mode == "MOCK":
            return {"ok": True, "sku": sku, "stock": 999}
        # REAL → requests.get(...) (omito por brevedad)
        return {"ok": True, "sku": sku, "stock": 10}

    def reservar(self, ot: str, taller: str, items: List[Item], usuario: str) -> Dict[str, Any]:
        if self.mode != "REAL":
            return self._mock_ok(action="reservar", ot=ot, taller=taller, items=[i.__dict__ for i in items])
        # REAL: requests.post(...)

    def entregar(self, ot: str, taller: str, items: List[Item], usuario: str) -> Dict[str, Any]:
        if self.mode != "REAL":
            return self._mock_ok(action="entregar", ot=ot, taller=taller, items=[i.__dict__ for i in items])
        # REAL: requests.post(...)

    def anular(self, mov_id: str, motivo: str, usuario: str) -> Dict[str, Any]:
        if self.mode != "REAL":
            return self._mock_ok(action="anular", mov_id=mov_id, motivo=motivo)
        # REAL: requests.post(...)
