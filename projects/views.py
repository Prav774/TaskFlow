from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Sum
from django.conf import settings

from .models import Project, Segment, ActivityLog
from .forms import (
    ProjectForm, SegmentForm, SegmentProgressForm, 
    SegmentSubmitForm, SegmentReassignForm, RejectionForm, ProjectRatingForm
)
from accounts.decorators import admin_required, employee_required
from notifications.models import Notification


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# Admin Views

@login_required
@admin_required
def project_list(request):
    projects = Project.objects.filter(is_active=True)
    
    # Search
    search = request.GET.get('search', '')
    if search:
        projects = projects.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        projects = projects.filter(status=status)
    
    # Filter by priority
    priority = request.GET.get('priority', '')
    if priority:
        projects = projects.filter(priority=priority)
    
    projects = projects.order_by('-created_at')
    
    return render(request, 'projects/project_list.html', {
        'projects': projects,
        'search': search,
        'current_status': status,
        'current_priority': priority,
    })


@login_required
@admin_required
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.status = 'planning'
            project.save()
            
            ActivityLog.objects.create(
                user=request.user,
                action='create_project',
                description=f'Created project: {project.title}',
                ip_address=get_client_ip(request),
                project=project
            )
            
            messages.success(request, f'Project "{project.title}" created! Now add segments.')
            return redirect('projects:project_detail', pk=project.pk)
    else:
        form = ProjectForm()
    
    return render(request, 'projects/project_form.html', {'form': form, 'title': 'Create Project'})


@login_required
@admin_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk, is_active=True)
    segments = project.segments.filter(is_active=True).select_related('assigned_to')
    
    total_weight = project.get_total_weight()
    remaining_weight = 100 - total_weight
    
    return render(request, 'projects/project_detail.html', {
        'project': project,
        'segments': segments,
        'total_weight': total_weight,
        'remaining_weight': remaining_weight,
    })


@login_required
@admin_required
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk, is_active=True)
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            
            ActivityLog.objects.create(
                user=request.user,
                action='update_project',
                description=f'Updated project: {project.title}',
                ip_address=get_client_ip(request),
                project=project
            )
            
            messages.success(request, 'Project updated successfully!')
            return redirect('projects:project_detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project)
    
    return render(request, 'projects/project_form.html', {
        'form': form, 
        'title': 'Edit Project',
        'project': project
    })


@login_required
@admin_required
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk, is_active=True)
    
    if request.method == 'POST':
        project.is_active = False
        project.save()
        
        # Also soft delete segments
        project.segments.update(is_active=False)
        
        ActivityLog.objects.create(
            user=request.user,
            action='delete_project',
            description=f'Deleted project: {project.title}',
            ip_address=get_client_ip(request),
            project=project
        )
        
        messages.success(request, f'Project "{project.title}" deleted.')
        return redirect('projects:project_list')
    
    return render(request, 'projects/project_confirm_delete.html', {'project': project})


@login_required
@admin_required
def segment_add(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk, is_active=True)
    
    if request.method == 'POST':
        form = SegmentForm(request.POST, project=project)
        if form.is_valid():
            segment = form.save(commit=False)
            segment.project = project
            segment.save()
            
            # Update project status
            if project.status == 'planning':
                project.status = 'in_progress'
                project.save()
            
            # Notify employee
            if segment.assigned_to:
                Notification.objects.create(
                    user=segment.assigned_to,
                    notification_type='assignment',
                    title='New Segment Assigned',
                    message=f'You have been assigned "{segment.name}" in project "{project.title}"',
                    related_segment=segment
                )
            
            ActivityLog.objects.create(
                user=request.user,
                action='create_segment',
                description=f'Added segment "{segment.name}" to {project.title}',
                ip_address=get_client_ip(request),
                project=project,
                segment=segment
            )
            
            # Check if weight is complete
            total_weight = project.get_total_weight()
            if total_weight == 100:
                messages.success(request, f'Segment added! Total weight is now 100%.')
            else:
                messages.success(request, f'Segment added! Total weight: {total_weight}%. Add more segments to reach 100%.')
            
            return redirect('projects:project_detail', pk=project.pk)
    else:
        form = SegmentForm(project=project)
    
    total_weight = project.get_total_weight()
    remaining = 100 - total_weight
    
    return render(request, 'projects/segment_form.html', {
        'form': form,
        'project': project,
        'title': 'Add Segment',
        'remaining_weight': remaining,
    })


@login_required
@admin_required
def segment_detail_admin(request, pk):
    segment = get_object_or_404(Segment, pk=pk, is_active=True)
    
    return render(request, 'projects/segment_detail_admin.html', {'segment': segment})


@login_required
@admin_required
def segment_approve(request, pk):
    segment = get_object_or_404(Segment, pk=pk, is_active=True, status='submitted')
    
    segment.status = 'approved'
    segment.approved_at = timezone.now()
    segment.save()
    
    # Notify employee
    Notification.objects.create(
        user=segment.assigned_to,
        notification_type='approval',
        title='Segment Approved',
        message=f'Your segment "{segment.name}" has been approved!',
        related_segment=segment
    )
    
    ActivityLog.objects.create(
        user=request.user,
        action='approve_segment',
        description=f'Approved segment "{segment.name}" in {segment.project.title}',
        ip_address=get_client_ip(request),
        project=segment.project,
        segment=segment
    )
    
    messages.success(request, f'Segment "{segment.name}" approved!')
    return redirect('accounts:admin_dashboard')


@login_required
@admin_required
def segment_reject(request, pk):
    segment = get_object_or_404(Segment, pk=pk, is_active=True, status='submitted')
    
    if request.method == 'POST':
        form = RejectionForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data['reason']
            
            segment.status = 'rejected'
            segment.rejection_count += 1
            segment.rejection_reason = reason
            segment.progress = 0  # Reset progress
            segment.save()
            
            # Check if max rejections reached
            if segment.rejection_count >= settings.MAX_REJECTIONS:
                segment.status = 'failed'
                segment.save()
                
                Notification.objects.create(
                    user=request.user,
                    notification_type='system',
                    title='Segment Failed',
                    message=f'Segment "{segment.name}" has reached max rejections. Please reassign.',
                    related_segment=segment
                )
            
            # Notify employee
            Notification.objects.create(
                user=segment.assigned_to,
                notification_type='rejection',
                title='Segment Rejected',
                message=f'Your segment "{segment.name}" was rejected. Reason: {reason}',
                related_segment=segment
            )
            
            ActivityLog.objects.create(
                user=request.user,
                action='reject_segment',
                description=f'Rejected segment "{segment.name}": {reason}',
                ip_address=get_client_ip(request),
                project=segment.project,
                segment=segment
            )
            
            messages.warning(request, f'Segment rejected. Rejection count: {segment.rejection_count}/{settings.MAX_REJECTIONS}')
            return redirect('accounts:admin_dashboard')
    else:
        form = RejectionForm()
    
    return render(request, 'projects/segment_reject.html', {
        'form': form,
        'segment': segment,
    })


@login_required
@admin_required
def segment_reassign(request, pk):
    segment = get_object_or_404(Segment, pk=pk, is_active=True)
    old_employee = segment.assigned_to
    
    if request.method == 'POST':
        form = SegmentReassignForm(request.POST, segment=segment)
        if form.is_valid():
            new_employee = form.cleaned_data['new_employee']
            
            segment.assigned_to = new_employee
            segment.save()
            
            # Notify old employee
            if old_employee:
                Notification.objects.create(
                    user=old_employee,
                    notification_type='reassignment',
                    title='Segment Reassigned',
                    message=f'Segment "{segment.name}" has been reassigned to another employee.',
                    related_segment=segment
                )
            
            # Notify new employee
            Notification.objects.create(
                user=new_employee,
                notification_type='assignment',
                title='New Segment Assigned',
                message=f'You have been assigned "{segment.name}" in project "{segment.project.title}"',
                related_segment=segment
            )
            
            ActivityLog.objects.create(
                user=request.user,
                action='reassign_segment',
                description=f'Reassigned "{segment.name}" from {old_employee} to {new_employee}',
                ip_address=get_client_ip(request),
                project=segment.project,
                segment=segment
            )
            
            messages.success(request, f'Segment reassigned to {new_employee.get_full_name() or new_employee.username}')
            return redirect('projects:segment_detail_admin', pk=segment.pk)
    else:
        form = SegmentReassignForm(segment=segment)
    
    return render(request, 'projects/segment_reassign.html', {
        'form': form,
        'segment': segment,
    })


@login_required
@admin_required
def project_rate(request, pk):
    project = get_object_or_404(Project, pk=pk, is_active=True, status='completed')
    
    if request.method == 'POST':
        form = ProjectRatingForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project rated successfully!')
            return redirect('projects:project_detail', pk=project.pk)
    else:
        form = ProjectRatingForm(instance=project)
    
    return render(request, 'projects/project_rate.html', {
        'form': form,
        'project': project,
    })


@login_required
@admin_required
def all_segments(request):
    segments = Segment.objects.filter(is_active=True).select_related('project', 'assigned_to')
    
    status = request.GET.get('status', '')
    if status:
        segments = segments.filter(status=status)
    
    segments = segments.order_by('-updated_at')
    
    return render(request, 'projects/all_segments.html', {
        'segments': segments,
        'current_status': status,
    })


# Employee Views

@login_required
@employee_required
def segment_detail_employee(request, pk):
    segment = get_object_or_404(
        Segment, 
        pk=pk, 
        assigned_to=request.user,
        is_active=True
    )
    
    return render(request, 'projects/segment_detail_employee.html', {'segment': segment})


@login_required
@employee_required
def segment_update_progress(request, pk):
    segment = get_object_or_404(
        Segment,
        pk=pk,
        assigned_to=request.user,
        is_active=True
    )
    
    if segment.status == 'approved':
        messages.error(request, 'Cannot update an approved segment.')
        return redirect('projects:segment_detail_employee', pk=pk)
    
    if request.method == 'POST':
        progress = request.POST.get('progress', 0)
        try:
            progress = int(progress)
            if 0 <= progress <= 100:
                # Check max active segments when starting work
                if segment.status == 'pending' and progress > 0:
                    if not request.user.can_take_more_segments():
                        messages.error(request, f'You already have {settings.MAX_ACTIVE_SEGMENTS} active segments.')
                        return redirect('projects:segment_detail_employee', pk=pk)
                    segment.status = 'in_progress'
                
                segment.progress = progress
                segment.last_progress_update = timezone.now()
                segment.save()
                
                ActivityLog.objects.create(
                    user=request.user,
                    action='update_progress',
                    description=f'Updated progress on "{segment.name}" to {progress}%',
                    ip_address=get_client_ip(request),
                    project=segment.project,
                    segment=segment
                )
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'progress': progress})
                
                messages.success(request, f'Progress updated to {progress}%')
        except ValueError:
            messages.error(request, 'Invalid progress value.')
    
    return redirect('projects:segment_detail_employee', pk=pk)


@login_required
@employee_required
def segment_submit(request, pk):
    segment = get_object_or_404(
        Segment,
        pk=pk,
        assigned_to=request.user,
        is_active=True
    )
    
    if segment.status == 'approved':
        messages.error(request, 'This segment is already approved.')
        return redirect('projects:segment_detail_employee', pk=pk)
    
    if segment.progress < 100:
        messages.error(request, 'Progress must be 100% before submitting.')
        return redirect('projects:segment_detail_employee', pk=pk)
    
    if request.method == 'POST':
        form = SegmentSubmitForm(request.POST, request.FILES, instance=segment)
        if form.is_valid():
            segment = form.save(commit=False)
            segment.status = 'submitted'
            segment.submitted_at = timezone.now()
            segment.save()
            
            # Notify admin
            from accounts.models import User
            admins = User.objects.filter(role='admin')
            for admin in admins:
                Notification.objects.create(
                    user=admin,
                    notification_type='submission',
                    title='New Submission',
                    message=f'{request.user.get_full_name() or request.user.username} submitted "{segment.name}"',
                    related_segment=segment
                )
            
            ActivityLog.objects.create(
                user=request.user,
                action='submit_segment',
                description=f'Submitted segment "{segment.name}" for approval',
                ip_address=get_client_ip(request),
                project=segment.project,
                segment=segment
            )
            
            messages.success(request, 'Segment submitted for approval!')
            return redirect('accounts:employee_dashboard')
    else:
        form = SegmentSubmitForm(instance=segment)
    
    return render(request, 'projects/segment_submit.html', {
        'form': form,
        'segment': segment,
    })


@login_required
@employee_required
def my_history(request):
    segments = Segment.objects.filter(
        assigned_to=request.user,
        is_active=True,
        status='approved'
    ).select_related('project').order_by('-approved_at')
    
    return render(request, 'projects/my_history.html', {'segments': segments})
