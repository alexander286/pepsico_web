
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
    ,ot_solicitar_repuesto, ot_guardar_observaciones, ot_checklist_toggle, ot_confirmar_entrega, mecanico_dashboard

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

    path("ots/<str:numero_ot>/solicitud/<int:solicitud_id>/confirmar-entrega/",ot_confirmar_entrega, name="ot_confirmar_entrega")

    
]
