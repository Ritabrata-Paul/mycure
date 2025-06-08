from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
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
    
    # Patient Information Fields
    patient_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name'
        })
    )
    patient_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    patient_phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your contact number'
        })
    )
    GENDER_CHOICES = (
        ('', 'Select Gender'),
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    patient_gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    patient_age = forms.IntegerField(
        min_value=1,
        max_value=120,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your age',
            'min': '1',
            'max': '120'
        })
    )

    # Appointment Details
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Additional notes for the appointment (symptoms, concerns, etc.)'
        })
    )
    appointment_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'min': timezone.now().date().isoformat(),
            'id': 'appointment-date'
        })
    )
    
    # Change this to CharField instead of ChoiceField to avoid validation issues
    slot_id = forms.CharField(
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'time-slot-select'
        })
    )

    class Meta:
        model = Appointment
        fields = ['notes', 'appointment_date']

    def __init__(self, service_id=None, user=None, *args, **kwargs):
        super(BookAppointmentForm, self).__init__(*args, **kwargs)
        
        # Store service_id for validation
        self.service_id = service_id
        
        # Pre-populate user information if user is provided
        if user:
            self.fields['patient_name'].initial = user.get_full_name()
            self.fields['patient_email'].initial = user.email
            if hasattr(user, 'phone_number') and user.phone_number:
                self.fields['patient_phone'].initial = user.phone_number

        # Set initial widget choices for time slots
        self.fields['slot_id'].widget.choices = [('', 'First select a date to see available time slots')]

    def clean_slot_id(self):
        """Custom validation for slot_id"""
        slot_id = self.cleaned_data.get('slot_id')
        
        if not slot_id:
            raise ValidationError("Please select a time slot.")
        
        try:
            # Convert to integer and validate that the time slot exists
            slot_id = int(slot_id)
            time_slot = TimeSlot.objects.get(id=slot_id, is_active=True)
            
            # Verify the time slot belongs to the service
            if self.service_id:
                service = Service.objects.get(id=self.service_id)
                if not time_slot.services.filter(id=service.id).exists():
                    raise ValidationError("The selected time slot is not available for this service.")
            
            return slot_id
            
        except (ValueError, TypeError):
            raise ValidationError("Invalid time slot selected.")
        except TimeSlot.DoesNotExist:
            raise ValidationError("The selected time slot is no longer available.")
        except Service.DoesNotExist:
            raise ValidationError("Service not found.")

    def clean(self):
        cleaned_data = super().clean()
        appointment_date = cleaned_data.get('appointment_date')
        slot_id = cleaned_data.get('slot_id')
        
        if appointment_date and slot_id:
            try:
                # Get the selected time slot
                time_slot = TimeSlot.objects.get(id=slot_id)
                
                # Get the weekday of the selected date (0=Monday, 6=Sunday)
                selected_weekday = appointment_date.weekday()
                
                # Check if the time slot's weekday matches the selected date's weekday
                if time_slot.weekday != selected_weekday:
                    weekday_names = {
                        0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday',
                        4: 'Friday', 5: 'Saturday', 6: 'Sunday'
                    }
                    selected_day_name = weekday_names[selected_weekday]
                    slot_day_name = weekday_names[time_slot.weekday]
                    
                    raise ValidationError(
                        f"The selected time slot is for {slot_day_name}, but you selected {selected_day_name}. "
                        f"Please select a time slot that matches your chosen date."
                    )
                
                # Check if the slot is already booked for this date
                from .models import AppointmentSlot
                existing_slot = AppointmentSlot.objects.filter(
                    time_slot=time_slot,
                    date=appointment_date
                ).first()
                
                if existing_slot:
                    raise ValidationError("This time slot is already booked for the selected date. Please choose another slot.")
                        
            except TimeSlot.DoesNotExist:
                raise ValidationError("Invalid time slot selected.")
        
        return cleaned_data

    def clean_patient_phone(self):
        phone = self.cleaned_data.get('patient_phone')
        if phone:
            # Remove any non-digit characters for validation
            phone_digits = ''.join(filter(str.isdigit, phone))
            if len(phone_digits) < 10:
                raise forms.ValidationError("Please enter a valid phone number with at least 10 digits.")
        return phone

    def clean_patient_age(self):
        age = self.cleaned_data.get('patient_age')
        if age and (age < 1 or age > 120):
            raise forms.ValidationError("Please enter a valid age between 1 and 120.")
        return age