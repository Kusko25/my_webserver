from django.contrib import admin
from django.http import HttpResponse
import my_dashboard.models as mdl
import csv


# Register your models here.

@admin.register(mdl.EventPlantWatering)
class AdminEventPlantWatering(admin.ModelAdmin):
    list_display = ['plant', 'value', 'unit', 'timestamp']
    list_filter = ['plant', 'unit']
    actions = ['export_as_csv']
    
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])

        return response
    
    export_as_csv.short_description = "Export selected as CSV"

for model in [
    mdl.Movie, 
    mdl.MovieInstance, 
    mdl.TVShow, 
    mdl.TVShowEpisode, 
    mdl.TVShowEpisodeInstance, 
    mdl.EventMedication, 
    mdl.EventExercise, 
    mdl.EventCalories,
    mdl.AppSettings, 
    mdl.ScheduleMedication, 
    mdl.ScheduleExercise,
    mdl.SchedulePlantWatering,
    ]:
    # list_display
    # Custom
    if model == mdl.AppSettings:
        list_display = ['key', 'value', 'value_type']
    elif model == mdl.EventCalories:
        list_display = ['value', 'unit', 'timestamp', 'description']
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
            if field.get_internal_type() == 'FloatField':
                list_display.append(field.name)
        for field in model._meta.fields:
            if field.get_internal_type() == 'DateField':
                list_display.append(field.name)
        for field in model._meta.fields:
            if field.get_internal_type() == 'DateTimeField':
                list_display.append(field.name)
    # list_filter
    # Custom
    if model == mdl.EventMedication:
        list_filter = ['medication']
    elif model == mdl.AppSettings:
        list_filter = ['value_type']
    elif model == mdl.MovieInstance:
        list_filter = ['movie', 'resolution', 'group']
    elif model == mdl.EventPlantWatering:
        list_filter = ['plant']
    elif model == mdl.EventCalories:
        list_filter = ['timestamp']
    else:
        # Default
        list_filter = []
    admin.site.register(model, list_display=list_display, list_filter=list_filter)
    # Display in overview in order ForeignKey, CharField, DateField

