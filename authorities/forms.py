from django import forms
from .models import Authority, Service, Doctor, TimeSlot

class AuthorityProfileForm(forms.ModelForm):
    """Form for updating authority profile"""
    name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
    city = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    state = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    postal_code = forms.CharField(  
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(  
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    website = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control'})
    )
    logo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    established_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    opening_time = forms.TimeField(
        initial='09:00',
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        help_text="Opening time (24-hour format)"
    )
    closing_time = forms.TimeField(
        initial='18:00',
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        help_text="Closing time (24-hour format)"
    )
    open_on_weekends = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Check if open on weekends"
    )

    registration_number = forms.CharField( 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    
    class Meta:
        model = Authority
        fields = ['name', 'description', 'address', 'city', 'state', 'postal_code',
                  'phone', 'website', 'logo', 'established_date', 'opening_time', 'closing_time', 'open_on_weekends','registration_number']
        
    def clean(self):
        cleaned_data = super().clean()
        opening_time = cleaned_data.get('opening_time')
        closing_time = cleaned_data.get('closing_time')
        
        # Validate that closing time is after opening time
        if opening_time and closing_time and opening_time >= closing_time:
            raise forms.ValidationError("Closing time must be after opening time.")
        
        return cleaned_data

class ServiceForm(forms.ModelForm):
    """Form for adding/editing services"""
    name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    price = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    duration_minutes = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    doctor = forms.ModelChoiceField(
        queryset=Doctor.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_active = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = Service
        fields = ['name', 'description', 'price', 'duration_minutes', 'doctor', 'is_active']
    
    def __init__(self, authority=None, *args, **kwargs):
        super(ServiceForm, self).__init__(*args, **kwargs)
        
        # If authority is provided, filter doctors by authority
        if authority:
            self.fields['doctor'].queryset = Doctor.objects.filter(authority=authority)

class DoctorForm(forms.ModelForm):
    """Form for adding/editing doctors"""
    name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    specialization = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    qualification = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    experience_years = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    gender = forms.ChoiceField(
        choices=Doctor.GENDER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    consultation_fee = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Doctor
        fields = ['name', 'specialization', 'qualification', 'experience_years', 
                  'gender', 'email', 'phone', 'bio', 'consultation_fee', 'photo']

class TimeSlotForm(forms.ModelForm):
    """Form for adding/editing time slots"""
    services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True,
        help_text="Select one or more services for this time slot"
    )
    doctors = forms.ModelMultipleChoiceField(
        queryset=Doctor.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        help_text="Select one or more doctors for this time slot"
    )
    weekday = forms.ChoiceField(
        choices=TimeSlot.WEEKDAY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    capacity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    is_active = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = TimeSlot
        fields = ['services', 'doctors', 'weekday', 'start_time', 'end_time', 'capacity', 'is_active']

    def __init__(self, authority=None, *args, **kwargs):
        super(TimeSlotForm, self).__init__(*args, **kwargs)
        # If authority is provided, filter services and doctors by authority
        if authority:
            self.fields['services'].queryset = Service.objects.filter(authority=authority, is_active=True)
            self.fields['doctors'].queryset = Doctor.objects.filter(authority=authority, is_active=True)
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        weekday = cleaned_data.get('weekday')
        services = cleaned_data.get('services')
        doctors = cleaned_data.get('doctors')
        
        # Validate time range
        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError("End time must be after start time.")
        
        # Check for duplicate slots (same authority, weekday, start_time, end_time)
        if hasattr(self, 'authority'):
            existing_slots = TimeSlot.objects.filter(
                authority=self.authority,
                weekday=weekday,
                start_time=start_time,
                end_time=end_time
            )
            
            # If editing, exclude current slot from check
            if self.instance and self.instance.pk:
                existing_slots = existing_slots.exclude(pk=self.instance.pk)
            
            if existing_slots.exists():
                raise forms.ValidationError(
                    "A time slot with the same day and time already exists. "
                    "Please choose a different time or modify the existing slot."
                )
        
        return cleaned_data

class AppointmentResponseForm(forms.Form):
    """Form for responding to appointment requests"""
    STATUS_CHOICES = (
        ('APPROVED', 'Approve'),
        ('REJECTED', 'Reject'),
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False  # Make it optional since we're handling rejection separately
    )
    rejection_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 4,
            'placeholder': 'Please provide a detailed reason for rejecting this appointment. This information will be shared with the patient.'
        }),
        help_text='This field is required when rejecting an appointment.'
    )
    
    def clean_rejection_reason(self):
        rejection_reason = self.cleaned_data.get('rejection_reason', '').strip()
        
        # If this form is being used for rejection, make sure reason is provided
        if not rejection_reason:
            raise forms.ValidationError('Please provide a reason for rejection.')
        
        # Ensure minimum length
        if len(rejection_reason) < 10:
            raise forms.ValidationError('Please provide a more detailed reason (at least 10 characters).')
            
        return rejection_reason
    
    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        rejection_reason = cleaned_data.get('rejection_reason')
        
        # If status is REJECTED, rejection_reason is required
        if status == 'REJECTED' and not rejection_reason:
            self.add_error('rejection_reason', 'Please provide a reason for rejection.')
            
        return cleaned_data