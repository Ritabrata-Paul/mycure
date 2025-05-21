from django.db import models
from accounts.models import User
from authorities.models import Authority

# Import any models you need from the authorities app
# No need to redefine the Authority model here since it's already defined in authorities app

class AdminMetrics(models.Model):
    """Model to store admin dashboard metrics"""
    date = models.DateField(auto_now_add=True)
    total_users = models.IntegerField(default=0)
    total_authorities = models.IntegerField(default=0)
    total_appointments = models.IntegerField(default=0)
    authorities_verified = models.IntegerField(default=0)
    authorities_pending = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = 'Admin Metric'
        verbose_name_plural = 'Admin Metrics'
        db_table = 'admin_metrics'
        
    def __str__(self):
        return f"Metrics for {self.date}"