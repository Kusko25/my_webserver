import enum
import logging
from datetime import datetime, timedelta
from typing import ClassVar

from django.db import models
from django.utils import timezone

from .events import EventExercise, EventMedication, EventPlantWatering

logger = logging.getLogger(__name__)
class ScheduleMedication(models.Model):
    medication = models.CharField(max_length=200, choices=EventMedication.MEDICATIONS)
    unit = models.CharField(max_length=200, choices=EventMedication.UNITS, default='mg')
    value = models.FloatField()
    
    METHODS = (
        ('daily','Daily'),
        ('weekly','Weekly'),
        ('monthly','Monthly'),
        ('weekdays','Weekdays'),
    )
    method = models.CharField(max_length=200, choices=METHODS, default='daily')
    weekdays = models.JSONField(default=list, blank=True, null=False, help_text='0=Monday, 1=Tuesday, ..., 6=Sunday')
    
    class ReturnCodes(enum.Enum):
        NOT_SATISFIED = 0
        SATISFIED = 1
        CANT_BE_DETERMINED = 2
        OVERSATISFIED = 3
        NOT_RELEVANT = 4

    def __str__(self):
        if self.method == 'weekdays':
            if len(self.weekdays) == 7:
                return f'{self.medication} - {self.method} - Every day'
            elif self.weekdays == [0,1,2,3,4]:
                return f'{self.medication} - {self.method} - Weekdays'
            elif self.weekdays == [5,6]:
                return f'{self.medication} - {self.method} - Weekends'
            else:
                return f'{self.medication} - {self.method} - {", ".join(["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"][i] for i in self.weekdays)}'
        return f'{self.medication} - {self.method}'

    def is_satisfied(self):
        if self.method == 'daily':
            events = EventMedication.objects.filter(medication=self.medication, timestamp__date=timezone.now().date())
            matching_units = [event for event in events if event.unit == self.unit]
            sum_matching = sum([event.value for event in matching_units])
        elif self.method == 'weekly':
            events = EventMedication.objects.filter(medication=self.medication, timestamp__date_gte=timezone.now().date() - timedelta(days=7))
            matching_units = [event for event in events if event.unit == self.unit]
            sum_matching = sum([event.value for event in matching_units])
        elif self.method == 'monthly':
            events = EventMedication.objects.filter(medication=self.medication, timestamp__date_gte=timezone.now().date() - timedelta(days=30))
            matching_units = [event for event in events if event.unit == self.unit]
            sum_matching = sum([event.value for event in matching_units])
        elif self.method == 'weekdays':
            if timezone.now().weekday() in self.weekdays:
                events = EventMedication.objects.filter(medication=self.medication, timestamp__date=timezone.now().date())
                matching_units = [event for event in events if event.unit == self.unit]
                sum_matching = sum([event.value for event in matching_units])
            else:
                return ScheduleMedication.ReturnCodes.NOT_RELEVANT, None
        else:
            raise ValueError(f"Event method '{self.method}' does not exist.")
            
        if sum_matching == self.value:
            if len(matching_units) == len(events):
                return ScheduleMedication.ReturnCodes.SATISFIED, None
            else:
                return ScheduleMedication.ReturnCodes.OVERSATISFIED, None
        elif sum_matching < self.value:
            if len(matching_units) == len(events):
                return ScheduleMedication.ReturnCodes.NOT_SATISFIED, self.value - sum_matching
            else:
                return ScheduleMedication.ReturnCodes.CANT_BE_DETERMINED, None
        else:
            if len(matching_units) == len(events):
                return ScheduleMedication.ReturnCodes.OVERSATISFIED, sum_matching - self.value
            else:
                return ScheduleMedication.ReturnCodes.OVERSATISFIED, None
    
    def fulfill(self):
        return_code, delta = self.is_satisfied()
        if return_code == ScheduleMedication.ReturnCodes.NOT_SATISFIED:
            EventMedication.objects.create(
                unit=self.unit, 
                value=delta, 
                medication=self.medication, 
                timestamp=timezone.localtime(), 
                event_type='medication', 
                description='Fulfilled by schedule'
                )
            return True
        else:
            return False

class ScheduleExercise(models.Model):
    exercise = models.CharField(max_length=200, choices=EventExercise.EXERCISES)
    unit = models.CharField(max_length=200, choices=EventExercise.UNITS, default='minutes')
    value = models.FloatField()
    
    METHODS:ClassVar[list[tuple[str,str]]] = [
        ('daily','Daily'),
        ('weekly','Weekly'),
        ('monthly','Monthly'),
        ('weekdays','Weekdays'),
    ]
    method = models.CharField(max_length=200, choices=METHODS, default='daily')
    weekdays = models.JSONField(default=list, blank=True, null=False, help_text='0=Monday, 1=Tuesday, ..., 6=Sunday')

    
        
    DEFAULT_CHUNKS:ClassVar[dict[str,float]] = {
        'minutes': 20.0,
        'km': 5.0,
        'reps': 10.0,
    }

    # To make sure that the default chunks are set for all units
    for unit_ in EventExercise.UNITS:
        assert unit_[0] in DEFAULT_CHUNKS, f'Missing default chunk for unit: {unit_[0]}'
    
    class ReturnCodes(enum.Enum):
        NOT_SATISFIED = 0
        SATISFIED = 1
        CANT_BE_DETERMINED = 2
        OVERSATISFIED = 3
        NOT_RELEVANT = 4

    def __str__(self):
        if self.method == 'weekdays':
            if len(self.weekdays) == 7:
                return f'{self.exercise} - {self.method} - Every day'
            elif self.weekdays == [0,1,2,3,4]:
                return f'{self.exercise} - {self.method} - Weekdays'
            elif self.weekdays == [5,6]:
                return f'{self.exercise} - {self.method} - Weekends'
            else:
                return f'{self.exercise} - {self.method} - {", ".join([datetime.fromisoformat(str(day)).strftime("%A") for day in self.weekdays])}'
        return f'{self.exercise} - {self.method}'

    def is_satisfied(self):
        if self.method == 'daily':
            events = EventExercise.objects.filter(exercise=self.exercise, timestamp__date=timezone.now().date())
            matching_units = [event for event in events if event.unit == self.unit]
            sum_matching = sum([event.value for event in matching_units])
        elif self.method == 'weekly':
            events = EventExercise.objects.filter(exercise=self.exercise, timestamp__gte=timezone.now() - timedelta(days=7))
            matching_units = [event for event in events if event.unit == self.unit]
            sum_matching = sum([event.value for event in matching_units])
        elif self.method == 'monthly':
            events = EventExercise.objects.filter(exercise=self.exercise, timestamp__date_gte=timezone.now().date() - timedelta(days=30))
            matching_units = [event for event in events if event.unit == self.unit]
            sum_matching = sum([event.value for event in matching_units])
        elif self.method == 'weekdays':
            if timezone.now().weekday() in self.weekdays:
                events = EventExercise.objects.filter(exercise=self.exercise, timestamp__date=timezone.now().date())
                matching_units = [event for event in events if event.unit == self.unit]
                sum_matching = sum([event.value for event in matching_units])
            else:
                return ScheduleExercise.ReturnCodes.NOT_RELEVANT, None
        else:
            raise ValueError(f"Event method '{self.method}' does not exist.")
        
        if sum_matching == self.value:
            if len(matching_units) == len(events):
                return ScheduleExercise.ReturnCodes.SATISFIED, None
            else:
                return ScheduleExercise.ReturnCodes.OVERSATISFIED, None
        elif sum_matching < self.value:
            if len(matching_units) == len(events):
                return ScheduleExercise.ReturnCodes.NOT_SATISFIED, self.value - sum_matching
            else:
                return ScheduleExercise.ReturnCodes.CANT_BE_DETERMINED, None
        else:
            if len(matching_units) == len(events):
                return ScheduleExercise.ReturnCodes.OVERSATISFIED, sum_matching - self.value
            else:
                return ScheduleExercise.ReturnCodes.OVERSATISFIED, None
        
    def fulfill(self):
        EventExercise.objects.create(
            unit=self.unit, 
            value=self.DEFAULT_CHUNKS[self.unit],
            exercise=self.exercise, 
            timestamp=timezone.localtime(), 
            event_type='exercise', 
            description='Fulfilled by schedule'
            )
        return True

class SchedulePlantWatering(models.Model):
    plant = models.CharField(max_length=200, choices=EventPlantWatering.PLANTS)
    unit = models.CharField(max_length=200, choices=EventPlantWatering.UNITS, default='ml')
    value = models.FloatField()
    
    METHODS = (
        ('daily','Daily'),
        ('weekly','Weekly'),
        ('monthly','Monthly'),
        ('weekdays','Weekdays'),
    )
    method = models.CharField(max_length=200, choices=METHODS, default='daily')
    weekdays = models.JSONField(default=list, blank=True, null=False, help_text='0=Monday, 1=Tuesday, ..., 6=Sunday')
    
    DEFAULT_CHUNKS:ClassVar[dict[str,float]] = {
        'ml': 250.0,
        'l': 1.0,
    }

    # To make sure that the default chunks are set for all units
    for unit_ in EventPlantWatering.UNITS:
        assert unit_[0] in DEFAULT_CHUNKS, f'Missing default chunk for unit: {unit_[0]}'
    
    class ReturnCodes(enum.Enum):
        NOT_SATISFIED = 0
        SATISFIED = 1
        CANT_BE_DETERMINED = 2
        OVERSATISFIED = 3
        NOT_RELEVANT = 4

    def __str__(self):
        if self.method == 'weekdays':
            if len(self.weekdays) == 7:
                return f'{self.plant} - {self.method} - Every day'
            elif self.weekdays == [0,1,2,3,4]:
                return f'{self.plant} - {self.method} - Weekdays'
            elif self.weekdays == [5,6]:
                return f'{self.plant} - {self.method} - Weekends'
            else:
                # Weekday are represented as 0=Monday, 1=Tuesday, ..., 6=Sunday, turn that into actual names
                return f'{self.plant} - {self.method} - {", ".join([datetime.fromisoformat(f"2025-02-{3+day:02}").strftime("%A") for day in self.weekdays])}'
        return f'{self.plant} - {self.method}'

    def is_satisfied(self):
        if self.method == 'daily':
            events = EventPlantWatering.objects.filter(plant=self.plant, timestamp__date=timezone.now().date())
            matching_units = [event for event in events if event.unit == self.unit]
            sum_matching = sum([event.value for event in matching_units])
        elif self.method == 'weekly':
            events = EventPlantWatering.objects.filter(plant=self.plant, timestamp__gte=timezone.now() - timedelta(days=7))
            matching_units = [event for event in events if event.unit == self.unit]
            sum_matching = sum([event.value for event in matching_units])
        elif self.method == 'monthly':
            events = EventPlantWatering.objects.filter(plant=self.plant, timestamp__date_gte=timezone.now().date() - timedelta(days=30))
            matching_units = [event for event in events if event.unit == self.unit]
            sum_matching = sum([event.value for event in matching_units])
        elif self.method == 'weekdays':
            if timezone.now().weekday() in self.weekdays:
                events = EventPlantWatering.objects.filter(plant=self.plant, timestamp__date=timezone.now().date())
                matching_units = [event for event in events if event.unit == self.unit]
                sum_matching = sum([event.value for event in matching_units])
            else:
                return SchedulePlantWatering.ReturnCodes.NOT_RELEVANT, None
        else:
            raise ValueError(f"Event method '{self.method}' does not exist.")
        
        if sum_matching == self.value:
            if len(matching_units) == len(events):
                return SchedulePlantWatering.ReturnCodes.SATISFIED, None
            else:
                return SchedulePlantWatering.ReturnCodes.OVERSATISFIED, None
        elif sum_matching < self.value:
            if len(matching_units) == len(events):
                return SchedulePlantWatering.ReturnCodes.NOT_SATISFIED, self.value - sum_matching
            else:
                return SchedulePlantWatering.ReturnCodes.CANT_BE_DETERMINED, None
        else:
            if len(matching_units) == len(events):
                return SchedulePlantWatering.ReturnCodes.OVERSATISFIED, sum_matching - self.value
            else:
                return SchedulePlantWatering.ReturnCodes.OVERSATISFIED, None
        
    def fulfill(self):
        EventPlantWatering.objects.create(
            unit=self.unit, 
            value=self.DEFAULT_CHUNKS[self.unit],
            plant=self.plant, 
            timestamp=timezone.localtime(), 
            event_type="plant_watering", 
            description='Fulfilled by schedule'
            )
        return True
