from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
import os


def validate_file_size(value):
    filesize = value.size
    if filesize > settings.MAX_UPLOAD_SIZE:
        raise ValidationError(f'Maximum file size is {settings.MAX_UPLOAD_SIZE // (1024*1024)}MB')


class Project(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    deadline = models.DateTimeField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='planning')
    overall_progress = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_projects'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_active = models.BooleanField(default=True)
    
    # Rating after completion
    rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def calculate_progress(self):
        segments = self.segments.filter(is_active=True)
        if not segments.exists():
            return 0
        
        total = 0
        for segment in segments:
            if segment.status == 'approved':
                total += float(segment.weight)
            else:
                total += float(segment.weight) * float(segment.progress) / 100
        
        return round(total, 2)
    
    def update_progress(self):
        self.overall_progress = self.calculate_progress()
        self.save(update_fields=['overall_progress', 'updated_at'])
        
        # Check if all segments approved
        segments = self.segments.filter(is_active=True)
        if segments.exists() and all(s.status == 'approved' for s in segments):
            self.status = 'completed'
            self.save(update_fields=['status'])
    
    def get_total_weight(self):
        return self.segments.filter(is_active=True).aggregate(
            total=models.Sum('weight')
        )['total'] or 0
    
    @property
    def is_overdue(self):
        return self.deadline < timezone.now() and self.status != 'completed'


class Segment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('overdue', 'Overdue'),
        ('abandoned', 'Abandoned'),
        ('failed', 'Failed'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='segments')
    name = models.CharField(max_length=255)
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_segments'
    )
    deadline = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    progress = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(100)])
    
    # Deliverable
    deliverable_file = models.FileField(
        upload_to='deliverables/%Y/%m/',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'zip', 'doc', 'docx']),
            validate_file_size
        ]
    )
    deliverable_url = models.URLField(max_length=500, blank=True)
    
    # Rejection handling
    rejection_count = models.PositiveIntegerField(default=0)
    rejection_reason = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    last_progress_update = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['project', 'name']
    
    def __str__(self):
        return f"{self.project.title} - {self.name}"
    
    @property
    def effective_deadline(self):
        return self.deadline or self.project.deadline
    
    @property
    def is_overdue(self):
        deadline = self.effective_deadline
        return deadline < timezone.now() and self.status not in ['approved', 'completed']
    
    @property
    def has_deliverable(self):
        return bool(self.deliverable_file or self.deliverable_url)
    
    def can_submit(self):
        return self.progress == 100 and self.has_deliverable and self.status not in ['approved', 'failed']
    
    def clean(self):
        if self.status == 'submitted' and not self.has_deliverable:
            raise ValidationError('Cannot submit without a deliverable.')
    
    def save(self, *args, **kwargs):
        # Update progress timestamp
        if self.pk:
            old = Segment.objects.filter(pk=self.pk).first()
            if old and old.progress != self.progress:
                self.last_progress_update = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Update project progress
        if self.project:
            self.project.update_progress()


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create_project', 'Create Project'),
        ('update_project', 'Update Project'),
        ('delete_project', 'Delete Project'),
        ('create_segment', 'Create Segment'),
        ('update_segment', 'Update Segment'),
        ('assign_segment', 'Assign Segment'),
        ('reassign_segment', 'Reassign Segment'),
        ('submit_segment', 'Submit Segment'),
        ('approve_segment', 'Approve Segment'),
        ('reject_segment', 'Reject Segment'),
        ('update_progress', 'Update Progress'),
        ('create_employee', 'Create Employee'),
        ('auto_approve', 'Auto Approve'),
        ('mark_overdue', 'Mark Overdue'),
        ('mark_abandoned', 'Mark Abandoned'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activity_logs'
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Optional references
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    segment = models.ForeignKey(Segment, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"
