from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('accounts:login')
        if not request.user.is_admin_user:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('accounts:employee_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def employee_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('accounts:login')
        if not request.user.is_employee:
            messages.error(request, 'This page is only for employees.')
            return redirect('accounts:admin_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Please log in to access this page.')
                return redirect('accounts:login')
            if request.user.role not in allowed_roles:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('accounts:dashboard_redirect')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
