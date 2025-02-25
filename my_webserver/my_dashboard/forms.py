from typing import Any
from django import forms

from urllib.parse import urlparse

from .models import EventMedication, EventCalories, EventExercise

class GalleryViewerUrlForm(forms.Form):
    url = forms.URLField(label='URL', required=True)
    
    def clean_url(self):
        supported_domains = [
            'nortverse.com',
            'e-hentai.org',
        ]
        url = self.cleaned_data['url']
        parsed_url = urlparse(url)
        if parsed_url.netloc not in supported_domains:
            raise forms.ValidationError('Unsupported domain')
        return url

class CalorieEventForm(forms.ModelForm):
    class Meta:
        model = EventCalories
        fields = ['value', 'unit', 'description']
        labels = {
            'value': 'Amount',
            'unit': 'Unit',
            'description': 'Notes',
        }
        help_texts = {
        }
        error_messages = {
        }

class ExerciseEventForm(forms.ModelForm):
    timestamp = forms.DateTimeField(
        input_formats=['%d-%m-%Y %H:%M'],  # Add this line
        widget=forms.DateTimeInput(
            attrs={'class': 'datetimepicker'},
            format='%d-%m-%Y %H:%M'
        )
    )
    class Meta:
        model = EventExercise
        fields = ['timestamp', 'exercise', 'value', 'unit', 'description']
        widgets = {
            'exercise': forms.RadioSelect(),
        }
        labels = {
            'timestamp': 'Date and Time',
            'exercise': 'Exercise',
            'value': 'Amount',
            'unit': 'Unit',
            'description': 'Notes',
        }
        help_texts = {
        }
        error_messages = {
        }

class MedicationEventForm(forms.ModelForm):
    timestamp = forms.DateTimeField(
        input_formats=['%d-%m-%Y %H:%M'],  # Add this line
        widget=forms.DateTimeInput(
            attrs={'class': 'datetimepicker'},
            format='%d-%m-%Y %H:%M'
        )
    )
    class Meta:
        model = EventMedication
        fields = ['timestamp', 'medication', 'value', 'unit', 'description']
        widgets = {
            'medication': forms.RadioSelect(),
        }
        labels = {
            'timestamp': 'Date and Time',
            'medication': 'Medication',
            'value': 'Amount',
            'unit': 'Unit',
            'description': 'Notes',
        }
        help_texts = {
        }
        error_messages = {
        }
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        # self.fields['timestamp'].widget.attrs.update(
        #     {
        #         'class': 'datetimepicker'
        #     }
        # )
    
    def clean(self) -> Any:
        cleaned = super().clean()
        return cleaned