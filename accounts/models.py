from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('employee', 'Employee'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='employee')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    skills = models.TextField(blank=True, help_text='Comma-separated skills')
    
    class Meta:
        ordering = ['username']
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"
    
    @property
    def is_admin_user(self):
        return self.role == 'admin'
    
    @property
    def is_employee(self):
        return self.role == 'employee'
    
    def get_skill_list(self):
        if self.skills:
            return [s.strip() for s in self.skills.split(',')]
        return []
    
    def get_active_segment_count(self):
        return self.assigned_segments.filter(
            status__in=['in_progress', 'submitted']
        ).count()
    
    def can_take_more_segments(self):
        from django.conf import settings
        return self.get_active_segment_count() < settings.MAX_ACTIVE_SEGMENTS
