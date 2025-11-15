from . import views
from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.contrib import admin
from django.urls import path, include
from app_taller.views import (
    HomeView, LoginViewCustom, logout_view, role_dashboard,
    AdminDashboard, SupervisorDashboard, MecanicoDashboard, ChoferDashboard, IngresoNuevoView, 
    OTListView, OTDetalleView, ot_cambiar_estado, ot_asignar_mecanico, OTSupervisorListView,
    ot_cambiar_prioridad, vehiculo_cambiar_estado, ot_subir_adjuntos, OTMecanicoListView, ot_mecanico_accion, ot_entregar_repuesto
    ,ot_solicitar_repuesto, ot_guardar_observaciones, ot_checklist_toggle, ot_confirmar_entrega, mecanico_dashboard,
    admin_usuario_toggle_activo, admin_usuario_reset_password,
    admin_usuarios_panel,
    admin_usuario_cambiar_rol,
    admin_usuario_nuevo,  admin_excel_panel, admin_excel_export_usuarios, admin_excel_import_usuarios
    , admin_excel_export_vehiculos, admin_excel_import_vehiculos, admin_excel_export_ots, admin_excel_import_ots,
    admin_excel_export_solicitudes, admin_excel_import_solicitudes,
    admin_excel_export_repuestos,admin_excel_import_repuestos, admin_excel_export_movimientos,admin_excel_import_movimientos,
    password_change_forzada, admin_excel_export_usuarios
    
    


)




urlpatterns = [
    path("", lambda r: redirect("home"), name="root"),
    path('admin/', admin.site.urls),
    
    path('home', HomeView.as_view(), name='home'),
    path('login', LoginViewCustom.as_view(), name='login'),
    path('logout', logout_view, name='logout'),
    
    # redirección por rol (genérica)
    path('dashboard', role_dashboard, name='dashboard'),
    # dashboards por rol (placeholders)
    path('dashboard/admin', AdminDashboard.as_view(), name='dashboard_admin'),
        # Acciones de administración de usuarios (panel propio, distinto del /admin de Django)
    path( "panel-admin/usuarios/<int:usuario_id>/toggle/",admin_usuario_toggle_activo, name="admin_usuario_toggle_activo",  ),
    path("panel-admin/usuarios/<int:usuario_id>/reset-pass/",admin_usuario_reset_password,name="admin_usuario_reset_password", ),
    path(
    "panel-admin/usuarios/",
    admin_usuarios_panel,
    name="admin_usuarios_panel"
    ),
    path(
        "panel-admin/usuarios/<int:usuario_id>/cambiar-rol/",
        admin_usuario_cambiar_rol,
        name="admin_usuario_cambiar_rol"
    ),

    path("panel-admin/usuarios/nuevo/", admin_usuario_nuevo, name="admin_usuario_nuevo"),  




    path('dashboard/supervisor', SupervisorDashboard.as_view(), name='dashboard_supervisor'),
    path('dashboard/mecanico', mecanico_dashboard, name='dashboard_mecanico'),
    path('dashboard/chofer', ChoferDashboard.as_view(), name='dashboard_chofer'),


    path("ingresos/nuevo", IngresoNuevoView.as_view(), name="ingreso_nuevo"),

    #ots 
    path("ots/", OTListView.as_view(), name="ot_list"), #DONDE ESTAN LOS FILTROS SUPER OT
        #vista supervisotr primero que el detalle
    path("ots/supervisor/", OTSupervisorListView.as_view(), name="ot_supervisor_list"), # VISTA DEL SUPERVISOR AL ABRIR LA OTS-->

    path("ots/<str:numero_ot>/", OTDetalleView.as_view(), name="ot_detalle"), #APARTADO PARA ACCIONES 
    path("ots/<str:numero_ot>/cambiar-estado/", ot_cambiar_estado, name="ot_cambiar_estado"), #APARTADO CAMBIO DE ESTADO O PROCESO
    path("ots/<str:numero_ot>/asignar-mecanico/", ot_asignar_mecanico, name="ot_asignar_mecanico"), #ASIGNA MECANICO 
    path("ots/<str:numero_ot>/cambiar-prioridad/", ot_cambiar_prioridad, name="ot_cambiar_prioridad"),
    path("ots/<str:numero_ot>/vehiculo/cambiar-estado/", vehiculo_cambiar_estado, name="vehiculo_cambiar_estado"),
    path("ots/<str:numero_ot>/adjuntos/subir/", ot_subir_adjuntos, name="ot_subir_adjuntos"),


    #mecanico 
    path("dashboard/mecanico/ots", OTMecanicoListView.as_view(), name="ot_mecanico_list"),
    path("ots/<str:numero_ot>/mecanico/<str:accion>/", ot_mecanico_accion, name="ot_mecanico_accion"),
    path("ots/<str:numero_ot>/entrega/", ot_entregar_repuesto, name="ot_entregar_repuesto"),

    path("ots/<str:numero_ot>/solicitar-repuesto/", ot_solicitar_repuesto, name="ot_solicitar_repuesto"),

    path("ots/<str:numero_ot>/observaciones/guardar/", ot_guardar_observaciones, name="ot_guardar_observaciones"),

   path("ots/<str:numero_ot>/checklist/toggle/", ot_checklist_toggle, name="ot_checklist_toggle"),

    path("ots/<str:numero_ot>/solicitud/<int:solicitud_id>/confirmar-entrega/",ot_confirmar_entrega, name="ot_confirmar_entrega"),

        # Panel Excel admin
    path("panel-admin/excel/", views.admin_excel_panel, name="admin_excel_panel"),
    path("panel-admin/excel/usuarios/export/", views.admin_excel_export_usuarios, name="admin_excel_export_usuarios"),
    path("panel-admin/excel/usuarios/import/", views.admin_excel_import_usuarios, name="admin_excel_import_usuarios"),
    path("panel-admin/excel/vehiculos/export/", views.admin_excel_export_vehiculos, name="admin_excel_export_vehiculos"),
    path("panel-admin/excel/vehiculos/import/", views.admin_excel_import_vehiculos, name="admin_excel_import_vehiculos"),


    path("panel-admin/excel/ots/export/", admin_excel_export_ots, name="admin_excel_export_ots"),
    path("panel-admin/excel/ots/import/", admin_excel_import_ots,name="admin_excel_import_ots"),

    # Solicitudes de repuesto
    path("panel-admin/excel/solicitudes/export/", admin_excel_export_solicitudes,name="admin_excel_export_solicitudes"),
    path("panel-admin/excel/solicitudes/import/", admin_excel_import_solicitudes,name="admin_excel_import_solicitudes"),

    # Catálogo de repuestos
    path("panel-admin/excel/repuestos/export/", admin_excel_export_repuestos,name="admin_excel_export_repuestos"),
    path("panel-admin/excel/repuestos/import/", admin_excel_import_repuestos,name="admin_excel_import_repuestos"),

    # Movimientos de repuestos
    path("panel-admin/excel/movimientos/export/", admin_excel_export_movimientos,name="admin_excel_export_movimientos"),
    path("panel-admin/excel/movimientos/import/", admin_excel_import_movimientos,name="admin_excel_import_movimientos"),

    path("mi-cuenta/cambiar-clave/", password_change_forzada, name="password_change_forzada"),

]


