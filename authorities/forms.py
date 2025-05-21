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
    postal_code = forms.CharField(  # Changed from zipcode to postal_code to match model
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(  # Added phone field
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
    registration_number = forms.CharField(  # Added registration_number field
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Authority
        fields = ['name', 'description', 'address', 'city', 'state', 'postal_code',
                  'phone', 'website', 'logo', 'established_date', 'registration_number']

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
    service = forms.ModelChoiceField(
        queryset=Service.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    doctor = forms.ModelChoiceField(
        queryset=Doctor.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
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
        fields = ['service', 'doctor', 'weekday', 'start_time', 'end_time', 'capacity', 'is_active']
    
    def __init__(self, authority=None, *args, **kwargs):
        super(TimeSlotForm, self).__init__(*args, **kwargs)
        
        # If authority is provided, filter services and doctors by authority
        if authority:
            self.fields['service'].queryset = Service.objects.filter(authority=authority)
            self.fields['doctor'].queryset = Doctor.objects.filter(authority=authority)

class AppointmentResponseForm(forms.Form):
    """Form for responding to appointment requests"""
    STATUS_CHOICES = (
        ('APPROVED', 'Approve'),
        ('REJECTED', 'Reject'),
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    rejection_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 3,
            'placeholder': 'Reason for rejection (required only if rejecting)'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        rejection_reason = cleaned_data.get('rejection_reason')
        
        if status == 'REJECTED' and not rejection_reason:
            self.add_error('rejection_reason', 'Please provide a reason for rejection.')
            
        return cleaned_data