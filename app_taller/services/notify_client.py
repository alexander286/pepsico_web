
from django.conf import settings

class NotifyClient:
    def __init__(self):
        self.base = settings.NOTIFY_API_BASE
        self.token = settings.NOTIFY_API_TOKEN
        self.mode = settings.NOTIFY_API_MODE.upper()

    def send(self, canal: str, destinatarios: list[str], asunto: str, mensaje: str, meta=None):
        if self.mode != "REAL":
            # Log simulado
            return {"ok": True, "mock": True}
        # REAL: requests.post(...)
        return {"ok": True}
