from django.db import models
from accounts.models import User
from authorities.models import Authority, Service, TimeSlot, Doctor
from django.utils import timezone

class Appointment(models.Model):
    """Model for appointments booked by users"""
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )
    
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    authority = models.ForeignKey(Authority, on_delete=models.CASCADE, related_name='appointments')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, related_name='appointments', blank=True, null=True)
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.SET_NULL, related_name='appointments', null=True)
    
    # Patient Information with defaults for existing records
    patient_name = models.CharField(max_length=100, default='Unknown Patient')
    patient_email = models.EmailField(default='unknown@example.com')
    patient_phone = models.CharField(max_length=15, default='0000000000')
    patient_gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M')
    patient_age = models.PositiveIntegerField(default=25)
    
    # Appointment Details
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.patient_name} - {self.service.name} - {self.appointment_date} {self.appointment_time}"
    
    def is_upcoming(self):
        appointment_datetime = timezone.make_aware(
            timezone.datetime.combine(self.appointment_date, self.appointment_time)
        )
        return appointment_datetime > timezone.now()
    
    def can_cancel(self):
        return self.status in ['PENDING', 'APPROVED'] and self.is_upcoming()
    
    def get_gender_display_full(self):
        return dict(self.GENDER_CHOICES).get(self.patient_gender, '')
    
    class Meta:
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'
        db_table = 'appointments'
        ordering = ['-appointment_date', '-appointment_time']

class AppointmentSlot(models.Model):
    """Model for tracking booked slots"""
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name='booked_slots')
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='booked_slot')
    date = models.DateField()
    is_available = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.time_slot} - {self.date}"
    
    class Meta:
        verbose_name = 'Appointment Slot'
        verbose_name_plural = 'Appointment Slots'
        db_table = 'appointment_slots'
        unique_together = ('time_slot', 'date')