from django import forms
from django.contrib.auth.forms import UserCreationForm
from accounts.models import User
from authorities.models import Authority
from contact.models import ContactMessage

class UserForm(forms.ModelForm):
    """Form for managing users"""
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    user_type = forms.ChoiceField(
        choices=User.USER_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_active = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If editing an admin user, disable user_type field
        if self.instance and self.instance.user_type == 'ADMIN':
            self.fields['user_type'].widget.attrs['disabled'] = 'disabled'
            self.fields['user_type'].help_text = "Admin user type cannot be changed"

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'user_type', 'is_active']

class AdminCreateUserForm(UserCreationForm):
    """Form for creating users by admin"""
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    user_type = forms.ChoiceField(
        choices=User.USER_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'user_type', 'password1', 'password2']

class AuthorityCreationForm(forms.ModelForm):
    """Form for creating authority by admin"""
    name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    authority_type = forms.ChoiceField(
        choices=Authority.AUTHORITY_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
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
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    website = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control'})
    )
    established_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )


    # Timing fields
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

    latitude = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'})
    )
    longitude = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'})
    )
    logo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    registration_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    is_verified = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(user_type='AUTHORITY'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False  # Make user field optional
    )
    
    class Meta:
        model = Authority
        fields = ['name', 'authority_type', 'description', 'address', 'email', 'phone', 
                 'website', 'city', 'state', 'postal_code', 'opening_time', 'closing_time', 
                 'open_on_weekends', 'latitude', 'longitude', 'logo', 'established_date', 
                 'registration_number', 'is_verified', 'user']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make some fields optional
        self.fields['user'].required = False  # We'll handle this in the view based on account_type
        
    def clean(self):
        cleaned_data = super().clean()
        opening_time = cleaned_data.get('opening_time')
        closing_time = cleaned_data.get('closing_time')
        
        # Validate that closing time is after opening time
        if opening_time and closing_time and closing_time <= opening_time:
            raise forms.ValidationError("Closing time must be after opening time.")
            
        return cleaned_data

class ContactMessageReplyForm(forms.Form):
    """Form for replying to contact messages"""
    reply = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 5,
            'placeholder': 'Type your reply here...'
        }),
        label="Reply Message"
    )