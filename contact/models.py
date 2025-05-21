from django.db import models
from accounts.models import User

class ContactMessage(models.Model):
    """Model for contact form messages"""
    STATUS_CHOICES = (
        ('NEW', 'New'),
        ('READ', 'Read'),
        ('REPLIED', 'Replied'),
        ('RESOLVED', 'Resolved'),
        ('SPAM', 'Spam'),
    )
    
    name = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='contact_messages', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='NEW')
    reply = models.TextField(blank=True, null=True)
    replied_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='replied_messages', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.subject}"
    
    class Meta:
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
        db_table = 'contact_messages'
        ordering = ['-created_at']