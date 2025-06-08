from django.urls import path
from . import views

urlpatterns = [
    # Search and booking
    path('search/', views.search_view, name='search'),
    path('authority/<int:authority_id>/', views.authority_detail_view, name='authority_detail'),
    path('service/<int:service_id>/', views.service_detail_view, name='service_detail'),
    path('book/<int:service_id>/', views.book_appointment_view, name='book_appointment'),
    
    # User appointments
    path('my-appointments/', views.my_appointments_view, name='my_appointments'),
    path('appointment/<int:appointment_id>/', views.appointment_detail_view, name='appointment_detail'),
    path('appointment/<int:appointment_id>/cancel/', views.cancel_appointment_view, name='cancel_appointment'),

    path('ajax/get-slots/', views.get_available_slots, name='get_available_slots'),
]