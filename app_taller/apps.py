from django.apps import AppConfig






# app_taller/apps.py
from django.apps import AppConfig
from django.db.backends.signals import connection_created

def _sqlite_pragmas(sender, connection, **kwargs):
    if connection.vendor == "sqlite":
        cursor = connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")   # mejor concurrencia
        cursor.execute("PRAGMA synchronous=NORMAL;") # performance
        cursor.close()

class AppTallerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_taller"

    def ready(self):
        connection_created.connect(_sqlite_pragmas)
