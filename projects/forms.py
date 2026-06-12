from django import forms
from django.core.exceptions import ValidationError
from django.conf import settings
from .models import Project, Segment
from accounts.models import User


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'deadline', 'priority']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            base_class = 'w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent backdrop-blur-sm'
            field.widget.attrs['class'] = base_class
            
            if field_name == 'priority':
                field.widget.attrs['class'] += ' appearance-none'


class SegmentForm(forms.ModelForm):
    class Meta:
        model = Segment
        fields = ['name', 'weight', 'assigned_to', 'deadline']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        # Only show employees
        self.fields['assigned_to'].queryset = User.objects.filter(role='employee')
        self.fields['assigned_to'].required = True
        
        for field_name, field in self.fields.items():
            base_class = 'w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent backdrop-blur-sm'
            field.widget.attrs['class'] = base_class
    
    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight and self.project:
            current_total = self.project.get_total_weight()
            if self.instance.pk:
                current_total -= self.instance.weight
            
            if current_total + weight > 100:
                remaining = 100 - current_total
                raise ValidationError(f'Weight exceeds limit. Remaining weight available: {remaining}%')
        return weight
    
    def clean_assigned_to(self):
        employee = self.cleaned_data.get('assigned_to')
        if employee and not employee.can_take_more_segments():
            raise ValidationError(
                f'{employee.get_full_name() or employee.username} already has '
                f'{settings.MAX_ACTIVE_SEGMENTS} active segments. Cannot assign more.'
            )
        return employee


class SegmentProgressForm(forms.ModelForm):
    class Meta:
        model = Segment
        fields = ['progress']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['progress'].widget.attrs.update({
            'type': 'range',
            'min': '0',
            'max': '100',
            'class': 'w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider'
        })


class SegmentSubmitForm(forms.ModelForm):
    class Meta:
        model = Segment
        fields = ['deliverable_file', 'deliverable_url']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent backdrop-blur-sm'
    
    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get('deliverable_file')
        url = cleaned_data.get('deliverable_url')
        
        if not file and not url:
            raise ValidationError('Please provide either a file or a URL as deliverable.')
        
        return cleaned_data


class SegmentReassignForm(forms.Form):
    new_employee = forms.ModelChoiceField(
        queryset=User.objects.filter(role='employee'),
        label='Reassign to'
    )
    
    def __init__(self, *args, **kwargs):
        self.segment = kwargs.pop('segment', None)
        super().__init__(*args, **kwargs)
        
        self.fields['new_employee'].widget.attrs['class'] = 'w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent backdrop-blur-sm'
    
    def clean_new_employee(self):
        employee = self.cleaned_data.get('new_employee')
        if employee and not employee.can_take_more_segments():
            raise ValidationError(
                f'{employee.get_full_name() or employee.username} already has '
                f'{settings.MAX_ACTIVE_SEGMENTS} active segments.'
            )
        return employee


class RejectionForm(forms.Form):
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=True,
        label='Rejection Reason'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reason'].widget.attrs['class'] = 'w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent backdrop-blur-sm'


class ProjectRatingForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['rating', 'review']
        widgets = {
            'review': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rating'].widget.attrs['class'] = 'w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:ring-2 focus:ring-yellow-500'
        self.fields['review'].widget.attrs['class'] = 'w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-500'
