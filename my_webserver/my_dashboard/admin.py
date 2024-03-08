from django.contrib import admin
from .models import *

# Register your models here.
for model in [Movie, MovieInstance, TVShow, TVShowEpisode, TVShowEpisodeInstance, EventMedication, AppSettings, MedicationSchedule]:
    # list_display
    # Custom
    if model == AppSettings:
        list_display = ['key', 'value', 'value_type']
    else:
        # Default
        list_display = []
        for field in model._meta.fields:
            if field.get_internal_type() == 'ForeignKey':
                list_display.append(field.name)
        for field in model._meta.fields:
            if field.get_internal_type() == 'CharField':
                list_display.append(field.name)
        for field in model._meta.fields:
            if field.get_internal_type() == 'DateField':
                list_display.append(field.name)
    # list_filter
    # Custom
    if model == EventMedication:
        list_filter = ['medication']
    elif model == AppSettings:
        list_filter = ['value_type']
    elif model == MovieInstance:
        list_filter = ['movie', 'resolution', 'group']
    else:
        # Default
        list_filter = []
    admin.site.register(model, list_display=list_display, list_filter=list_filter)
    # Display in overview in order ForeignKey, CharField, DateField

