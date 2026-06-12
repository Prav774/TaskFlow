from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    # Admin views
    path('', views.project_list, name='project_list'),
    path('create/', views.project_create, name='project_create'),
    path('<int:pk>/', views.project_detail, name='project_detail'),
    path('<int:pk>/edit/', views.project_edit, name='project_edit'),
    path('<int:pk>/delete/', views.project_delete, name='project_delete'),
    path('<int:pk>/rate/', views.project_rate, name='project_rate'),
    path('<int:project_pk>/segments/add/', views.segment_add, name='segment_add'),
    
    # Segment admin views
    path('segments/', views.all_segments, name='all_segments'),
    path('segments/<int:pk>/admin/', views.segment_detail_admin, name='segment_detail_admin'),
    path('segments/<int:pk>/approve/', views.segment_approve, name='segment_approve'),
    path('segments/<int:pk>/reject/', views.segment_reject, name='segment_reject'),
    path('segments/<int:pk>/reassign/', views.segment_reassign, name='segment_reassign'),
    
    # Employee views
    path('segments/<int:pk>/', views.segment_detail_employee, name='segment_detail_employee'),
    path('segments/<int:pk>/progress/', views.segment_update_progress, name='segment_update_progress'),
    path('segments/<int:pk>/submit/', views.segment_submit, name='segment_submit'),
    path('my-history/', views.my_history, name='my_history'),
]
