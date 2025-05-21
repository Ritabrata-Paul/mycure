from django import forms
from django.utils import timezone
from .models import Appointment
from authorities.models import Service, Authority, Doctor, TimeSlot

class SearchForm(forms.Form):
    """Form for searching authorities, services, and doctors"""
    SEARCH_TYPE_CHOICES = (
        ('', 'All'),
        ('HOSPITAL', 'Hospital'),
        ('CLINIC', 'Clinic'),
        ('DIAGNOSTIC', 'Diagnostic Center'),
    )
    
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search for doctors, services, or healthcare facilities'
        })
    )
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Location (city, state)'
        })
    )
    authority_type = forms.ChoiceField(
        choices=SEARCH_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class BookAppointmentForm(forms.ModelForm):
    """Form for booking an appointment"""
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Additional notes for the appointment'
        })
    )
    appointment_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'min': timezone.now().date().isoformat()
        })
    )
    slot_id = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = Appointment
        fields = ['notes', 'appointment_date']
    
    def __init__(self, service_id=None, *args, **kwargs):
        super(BookAppointmentForm, self).__init__(*args, **kwargs)
        
        # If service_id is provided, populate available time slots
        if service_id:
            service = Service.objects.get(id=service_id)
            time_slots = TimeSlot.objects.filter(service=service, is_active=True)
            
            # Create choices based on time slots
            slot_choices = [(slot.id, f"{dict(TimeSlot.WEEKDAY_CHOICES)[slot.weekday]}: {slot.start_time.strftime('%I:%M %p')} - {slot.end_time.strftime('%I:%M %p')}") for slot in time_slots]
            self.fields['slot_id'].choices = slot_choices