from django.urls import path
from . import views
urlpatterns = [
    # Admin dashboard
    path('dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    
    # User management
    path('users/', views.manage_users_view, name='manage_users'),
    path('user/<int:user_id>/', views.user_detail_view, name='user_detail'),
    path('user/add/', views.add_user_view, name='add_user'),
    path('user/<int:user_id>/edit/', views.edit_user_view, name='edit_user'),
    path('user/<int:user_id>/delete/', views.delete_user_view, name='delete_user'),
    
    # Authority management
    path('authorities/', views.manage_authorities_view, name='manage_authorities'),
    path('authority/add/', views.add_authority_view, name='add_authority'),
    path('authority/<int:authority_id>/', views.authority_detail_view, name='admin_authority_detail'),
    path('authority/<int:authority_id>/edit/', views.edit_authority_view, name='edit_authority'),
    path('authority/<int:authority_id>/delete/', views.delete_authority_view, name='delete_authority'),
    path('authority/<int:authority_id>/verify/', views.verify_authority_view, name='verify_authority'),
    
    # Appointment management
    path('appointments/', views.all_appointments_view, name='all_appointments'),
    path('appointment/<int:appointment_id>/', views.appointment_detail_view, name='admin_appointment_detail'),
    path('appointment/<int:appointment_id>/update/', views.update_appointment_view, name='admin_update_appointment'),
    
    # Contact message management
    path('contact-messages/', views.contact_messages_view, name='contact_messages'),
    path('contact-message/<int:message_id>/', views.contact_message_detail_view, name='contact_message_detail'),
    path('contact-message/<int:message_id>/reply/', views.reply_contact_message_view, name='reply_contact_message'),
]