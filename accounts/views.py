from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta

from .models import User
from .forms import CustomAuthenticationForm, UserRegistrationForm, UserUpdateForm, EmployeeCreationForm
from .decorators import admin_required, employee_required
from projects.models import Project, Segment, ActivityLog


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Log activity
            ActivityLog.objects.create(
                user=user,
                action='login',
                description=f'{user.username} logged in',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('accounts:dashboard_redirect')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        ActivityLog.objects.create(
            user=request.user,
            action='logout',
            description=f'{request.user.username} logged out',
            ip_address=get_client_ip(request)
        )
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required
def dashboard_redirect(request):
    if request.user.is_admin_user:
        return redirect('accounts:admin_dashboard')
    return redirect('accounts:employee_dashboard')


@login_required
@admin_required
def admin_dashboard(request):
    # Stats
    total_projects = Project.objects.filter(is_active=True).count()
    active_projects = Project.objects.filter(is_active=True, status='in_progress').count()
    completed_projects = Project.objects.filter(is_active=True, status='completed').count()
    
    overdue_segments = Segment.objects.filter(
        is_active=True,
        deadline__lt=timezone.now(),
        status__in=['pending', 'in_progress', 'submitted']
    ).count()
    
    # Calculate average progress
    avg_progress = Project.objects.filter(is_active=True).aggregate(
        avg=Avg('overall_progress')
    )['avg'] or 0
    
    # Pending approvals
    pending_approvals = Segment.objects.filter(
        is_active=True,
        status='submitted'
    ).select_related('project', 'assigned_to').order_by('-submitted_at')[:10]
    
    # Recent projects
    recent_projects = Project.objects.filter(is_active=True).order_by('-created_at')[:5]
    
    # Employee workload
    employees = User.objects.filter(role='employee').annotate(
        active_segments=Count('assigned_segments', filter=Q(
            assigned_segments__status__in=['in_progress', 'submitted'],
            assigned_segments__is_active=True
        ))
    ).order_by('-active_segments')[:10]
    
    # Overdue segments list
    overdue_list = Segment.objects.filter(
        is_active=True,
        deadline__lt=timezone.now(),
        status__in=['pending', 'in_progress', 'submitted']
    ).select_related('project', 'assigned_to').order_by('deadline')[:5]
    
    context = {
        'total_projects': total_projects,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'overdue_segments': overdue_segments,
        'avg_progress': round(avg_progress, 1),
        'pending_approvals': pending_approvals,
        'recent_projects': recent_projects,
        'employees': employees,
        'overdue_list': overdue_list,
    }
    
    return render(request, 'accounts/admin_dashboard.html', context)


@login_required
@employee_required
def employee_dashboard(request):
    user = request.user
    
    # Get segments by status
    in_progress = Segment.objects.filter(
        assigned_to=user,
        is_active=True,
        status='in_progress'
    ).select_related('project').order_by('deadline')
    
    submitted = Segment.objects.filter(
        assigned_to=user,
        is_active=True,
        status='submitted'
    ).select_related('project').order_by('-submitted_at')
    
    approved = Segment.objects.filter(
        assigned_to=user,
        is_active=True,
        status='approved'
    ).select_related('project').order_by('-updated_at')[:5]
    
    rejected = Segment.objects.filter(
        assigned_to=user,
        is_active=True,
        status='rejected'
    ).select_related('project').order_by('-updated_at')
    
    pending = Segment.objects.filter(
        assigned_to=user,
        is_active=True,
        status='pending'
    ).select_related('project').order_by('deadline')
    
    overdue = Segment.objects.filter(
        assigned_to=user,
        is_active=True,
        status='overdue'
    ).select_related('project').order_by('deadline')
    
    # Stats
    total_assigned = Segment.objects.filter(assigned_to=user, is_active=True).count()
    completed_count = Segment.objects.filter(assigned_to=user, is_active=True, status='approved').count()
    active_count = user.get_active_segment_count()
    
    context = {
        'in_progress': in_progress,
        'submitted': submitted,
        'approved': approved,
        'rejected': rejected,
        'pending': pending,
        'overdue': overdue,
        'total_assigned': total_assigned,
        'completed_count': completed_count,
        'active_count': active_count,
        'max_active': 3,
    }
    
    return render(request, 'accounts/employee_dashboard.html', context)


@login_required
@admin_required
def employee_list(request):
    employees = User.objects.filter(role='employee').annotate(
        total_segments=Count('assigned_segments', filter=Q(assigned_segments__is_active=True)),
        active_segments=Count('assigned_segments', filter=Q(
            assigned_segments__status__in=['in_progress', 'submitted'],
            assigned_segments__is_active=True
        )),
        completed_segments=Count('assigned_segments', filter=Q(
            assigned_segments__status='approved',
            assigned_segments__is_active=True
        ))
    ).order_by('username')
    
    return render(request, 'accounts/employee_list.html', {'employees': employees})


@login_required
@admin_required
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeCreationForm(request.POST)
        if form.is_valid():
            employee = form.save()
            
            ActivityLog.objects.create(
                user=request.user,
                action='create_employee',
                description=f'Created employee: {employee.username}',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f'Employee {employee.username} created successfully!')
            return redirect('accounts:employee_list')
    else:
        form = EmployeeCreationForm()
    
    return render(request, 'accounts/employee_form.html', {'form': form, 'title': 'Create Employee'})


@login_required
@admin_required
def employee_detail(request, pk):
    employee = get_object_or_404(User, pk=pk, role='employee')
    
    segments = Segment.objects.filter(
        assigned_to=employee,
        is_active=True
    ).select_related('project').order_by('-updated_at')
    
    # Stats
    stats = {
        'total': segments.count(),
        'active': segments.filter(status__in=['in_progress', 'submitted']).count(),
        'completed': segments.filter(status='approved').count(),
        'rejected': segments.filter(status='rejected').count(),
    }
    
    return render(request, 'accounts/employee_detail.html', {
        'employee': employee,
        'segments': segments,
        'stats': stats,
    })


@login_required
def profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = UserUpdateForm(instance=request.user)
    
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
@admin_required
def activity_log(request):
    logs = ActivityLog.objects.all().select_related('user').order_by('-timestamp')[:500]
    return render(request, 'accounts/activity_log.html', {'logs': logs})


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
