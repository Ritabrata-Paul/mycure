from django.db import models
from accounts.models import User
from django.utils import timezone

class Authority(models.Model):
    """Model for authorities like clinics, hospitals and diagnostic centers"""
    AUTHORITY_TYPE_CHOICES = (
        ('HOSPITAL', 'Hospital'),
        ('CLINIC', 'Clinic'),
        ('DIAGNOSTIC', 'Diagnostic Center'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='authority_profile')
    name = models.CharField(max_length=255)
    authority_type = models.CharField(max_length=10, choices=AUTHORITY_TYPE_CHOICES)
    description = models.TextField()
    address = models.TextField()
    city = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    logo = models.ImageField(upload_to='authority_logos/', blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    established_date = models.DateField(blank=True, null=True)

    # Timing fields
    opening_time = models.TimeField(default='09:00', help_text="Opening time (24-hour format)")
    closing_time = models.TimeField(default='18:00', help_text="Closing time (24-hour format)")
    open_on_weekends = models.BooleanField(default=True, help_text="Check if open on weekends")
    
    is_verified = models.BooleanField(default=False)
    registration_number = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
        
    class Meta:
        verbose_name = 'Authority'
        verbose_name_plural = 'Authorities'
        db_table = 'authorities'


class Doctor(models.Model):
    """Model for doctors associated with authorities"""
    GENDER_CHOICES = (
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other'),
    )
    
    authority = models.ForeignKey(Authority, on_delete=models.CASCADE, related_name='doctors')
    name = models.CharField(max_length=255)
    specialization = models.CharField(max_length=255)
    qualification = models.CharField(max_length=255)
    experience_years = models.PositiveIntegerField()
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES)
    photo = models.ImageField(upload_to='doctor_photos/', blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"Dr. {self.name} - {self.specialization}"
        
    class Meta:
        verbose_name = 'Doctor'
        verbose_name_plural = 'Doctors'
        db_table = 'doctors'


class Service(models.Model):
    """Model for services offered by authorities"""
    authority = models.ForeignKey(Authority, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=255)
    description = models.TextField()
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, related_name='services', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_minutes = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.authority.name}"
        
    class Meta:
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
        db_table = 'services'


class TimeSlot(models.Model):
    """Model for available time slots for booking"""
    WEEKDAY_CHOICES = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )
    authority = models.ForeignKey(Authority, on_delete=models.CASCADE, related_name='time_slots')
    services = models.ManyToManyField(Service, related_name='time_slots')  # Changed to ManyToMany
    doctors = models.ManyToManyField(Doctor, related_name='time_slots', blank=True)  # Changed to ManyToMany
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    capacity = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    is_booked = models.BooleanField(default=False)  # New field to track if slot is booked
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        day = dict(self.WEEKDAY_CHOICES)[self.weekday]
        services_list = ", ".join([service.name for service in self.services.all()[:2]])
        if self.services.count() > 2:
            services_list += f" +{self.services.count() - 2} more"
        return f"{self.authority.name} - {services_list} - {day} {self.start_time} to {self.end_time}"
    
    class Meta:
        verbose_name = 'Time Slot'
        verbose_name_plural = 'Time Slots'
        db_table = 'time_slots'
        # Add unique constraint to prevent duplicate slots
        unique_together = ['authority', 'weekday', 'start_time', 'end_time']