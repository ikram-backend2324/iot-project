from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('devices/', views.device_list, name='device_list'),
    path('devices/add/', views.add_device, name='add_device'),
    path('devices/<int:pk>/', views.device_detail, name='device_detail'),
    path('devices/<int:pk>/edit/', views.edit_device, name='edit_device'),
    path('devices/<int:pk>/delete/', views.delete_device, name='delete_device'),
    path('devices/<int:pk>/metrics/add/', views.add_metric, name='add_metric'),
    path('devices/<int:pk>/analyze/', views.analyze_device, name='analyze_device'),
    path('analyses/', views.analysis_list, name='analysis_list'),
    path('analyses/<int:pk>/', views.analysis_detail, name='analysis_detail'),
    path('pc-check/', views.pc_check, name='pc_check'),
    path('pc-check/analyze/', views.pc_analyze, name='pc_analyze'),
    path('pc-check/result/<int:pk>/', views.pc_result, name='pc_result'),
    path('pc-check/agent/', views.pc_agent_download, name='pc_agent_download'),
]
