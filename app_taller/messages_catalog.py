# app_taller/messages_catalog.py

MSG = {
    # ───────── Login / permisos ─────────
    "no_permission": (
        "No dispone de los permisos necesarios para realizar esta acción."
    ),
    "access_denied": (
        "Su sesión no cuenta con autorización para acceder a este recurso."
    ),

    # ───────── Operaciones genéricas ─────────
    "saved_ok": "El registro se ha guardado correctamente.",
    "updated_ok": "La información ha sido actualizada correctamente.",
    "deleted_ok": "El registro se ha eliminado correctamente.",
    "unexpected_error": (
        "Se ha producido un error inesperado. "
        "Vuelva a intentarlo o contacte al administrador si el problema persiste."
    ),
    "invalid_form": (
        "La información ingresada no es válida. Revise los campos señalados."
    ),

    # ───────── Usuarios / cuentas ─────────
    "user_activated": "La cuenta del usuario ha sido activada correctamente.",
    "user_deactivated": (
        "La cuenta del usuario ha sido deshabilitada. "
        "El usuario no podrá acceder al sistema hasta ser reactivado."
    ),

    "user_not_found_for_login": (
        "No se encontró una cuenta de acceso asociada a este usuario. "
        "Verifique los datos o contacte al administrador del sistema."
    ),

    # Reseteo de contraseña
    "pwd_reset_ok": (
        "La contraseña temporal para {usuario} ha sido generada correctamente. "
        "Contraseña temporal: {password}. "
        "Solicite al usuario cambiarla en su próximo inicio de sesión."
    ),

    # ───────── Órdenes de trabajo ─────────
    "ot_not_found": "No se encontró la Orden de Trabajo solicitada.",
    "ot_created_ok": "La Orden de Trabajo ha sido creada correctamente.",
    "ot_state_changed": "El estado de la Orden de Trabajo ha sido actualizado.",
    "ot_priority_changed": "La prioridad de la Orden de Trabajo ha sido actualizada.",
    "ot_vehicle_state_changed": "El estado del vehículo ha sido actualizado.",

    # ───────── Repuestos / inventario ─────────
    "repuesto_request_ok": "La solicitud de repuesto ha sido registrada correctamente.",
    "repuesto_request_denied": (
        "No fue posible registrar la solicitud de repuesto. "
        "Revise la información ingresada."
    ),
    "repuesto_delivery_ok_api": (
        "La entrega de repuestos se registró correctamente en el inventario "
        "y en la Orden de Trabajo."
    ),
    "repuesto_delivery_ok_local": (
        "El inventario externo no se encuentra disponible. "
        "La entrega se registró localmente y queda pendiente de sincronización."
    ),
}
