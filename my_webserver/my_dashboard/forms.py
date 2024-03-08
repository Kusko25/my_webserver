from typing import Any
from datetime import datetime
from django import forms
from django.utils import timezone

from .models import EventMedication

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