from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_CHOICES = [
        ('assignment', 'Assignment'),
        ('submission', 'Submission'),
        ('approval', 'Approval'),
        ('rejection', 'Rejection'),
        ('overdue', 'Overdue'),
        ('reassignment', 'Reassignment'),
        ('system', 'System'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    related_segment = models.ForeignKey(
        'projects.Segment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    @property
    def icon(self):
        icons = {
            'assignment': '📋',
            'submission': '📤',
            'approval': '✅',
            'rejection': '❌',
            'overdue': '⏰',
            'reassignment': '🔄',
            'system': '⚙️',
        }
        return icons.get(self.notification_type, '📌')
