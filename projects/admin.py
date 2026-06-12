from django.contrib import admin
from .models import Project, Segment, ActivityLog


class SegmentInline(admin.TabularInline):
    model = Segment
    extra = 0
    fields = ['name', 'weight', 'assigned_to', 'status', 'progress']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'priority', 'deadline', 'overall_progress', 'is_active']
    list_filter = ['status', 'priority', 'is_active']
    search_fields = ['title', 'description']
    inlines = [SegmentInline]


@admin.register(Segment)
class SegmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'assigned_to', 'status', 'progress', 'weight']
    list_filter = ['status', 'is_active']
    search_fields = ['name', 'project__title']


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'timestamp', 'ip_address']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__username', 'description']
    readonly_fields = ['user', 'action', 'description', 'ip_address', 'timestamp', 'project', 'segment']
