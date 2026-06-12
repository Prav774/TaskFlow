from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from .models import Segment, ActivityLog
from notifications.models import Notification
from accounts.models import User


def check_auto_approval():
    """Auto-approve segments submitted more than 1 hour ago"""
    threshold = timezone.now() - timedelta(seconds=settings.AUTO_APPROVAL_TIMEOUT)
    
    segments = Segment.objects.filter(
        status='submitted',
        submitted_at__lt=threshold,
        is_active=True
    )
    
    for segment in segments:
        segment.status = 'approved'
        segment.approved_at = timezone.now()
        segment.save()
        
        # Notify employee
        if segment.assigned_to:
            Notification.objects.create(
                user=segment.assigned_to,
                notification_type='approval',
                title='Segment Auto-Approved',
                message=f'Your segment "{segment.name}" was auto-approved.',
                related_segment=segment
            )
        
        # Notify admins
        for admin in User.objects.filter(role='admin'):
            Notification.objects.create(
                user=admin,
                notification_type='system',
                title='Auto-Approval',
                message=f'Segment "{segment.name}" was auto-approved after 1 hour.',
                related_segment=segment
            )
        
        ActivityLog.objects.create(
            user=None,
            action='auto_approve',
            description=f'Auto-approved segment "{segment.name}" after timeout',
            project=segment.project,
            segment=segment
        )


def check_overdue_segments():
    """Mark overdue segments"""
    now = timezone.now()
    
    segments = Segment.objects.filter(
        is_active=True,
        status__in=['pending', 'in_progress', 'submitted']
    ).select_related('project')
    
    for segment in segments:
        deadline = segment.deadline or segment.project.deadline
        if deadline and deadline < now and segment.status != 'overdue':
            segment.status = 'overdue'
            segment.save()
            
            # Notify employee
            if segment.assigned_to:
                Notification.objects.create(
                    user=segment.assigned_to,
                    notification_type='overdue',
                    title='Segment Overdue',
                    message=f'Your segment "{segment.name}" is now overdue!',
                    related_segment=segment
                )
            
            # Notify admins
            for admin in User.objects.filter(role='admin'):
                Notification.objects.create(
                    user=admin,
                    notification_type='overdue',
                    title='Segment Overdue',
                    message=f'Segment "{segment.name}" assigned to {segment.assigned_to} is overdue.',
                    related_segment=segment
                )
            
            ActivityLog.objects.create(
                user=None,
                action='mark_overdue',
                description=f'Marked segment "{segment.name}" as overdue',
                project=segment.project,
                segment=segment
            )


def check_abandoned_segments():
    """Mark segments with no progress update for 14 days as abandoned"""
    threshold = timezone.now() - timedelta(days=settings.ABANDONED_DAYS)
    
    segments = Segment.objects.filter(
        is_active=True,
        status__in=['pending', 'in_progress'],
        last_progress_update__lt=threshold
    ).exclude(status='approved')
    
    # Also check segments that never had a progress update
    segments_never_updated = Segment.objects.filter(
        is_active=True,
        status__in=['pending', 'in_progress'],
        last_progress_update__isnull=True,
        created_at__lt=threshold
    ).exclude(status='approved')
    
    all_segments = segments | segments_never_updated
    
    for segment in all_segments:
        segment.status = 'abandoned'
        segment.save()
        
        # Notify admins
        for admin in User.objects.filter(role='admin'):
            Notification.objects.create(
                user=admin,
                notification_type='system',
                title='Segment Abandoned',
                message=f'Segment "{segment.name}" has been marked as abandoned. Please reassign.',
                related_segment=segment
            )
        
        ActivityLog.objects.create(
            user=None,
            action='mark_abandoned',
            description=f'Marked segment "{segment.name}" as abandoned after {settings.ABANDONED_DAYS} days of inactivity',
            project=segment.project,
            segment=segment
        )
