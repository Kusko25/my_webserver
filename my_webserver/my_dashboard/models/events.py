import logging
from datetime import datetime, timedelta
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.timezone import get_default_timezone as gdtz

from my_dashboard.models.misc import AppSettings

logger = logging.getLogger(__name__)

class Event(models.Model):
    event_type = models.CharField(max_length=200)
    timestamp = models.DateTimeField()
    value = models.TextField()
    unit = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.event_type} at {self.timestamp}'

    @classmethod
    def to_csv(cls):
        def clean_string(s):
            s = str(s)
            if ',' in s or '\n' in s:
                s = s.replace('"','""')
                s = '"' + s + '"'
            return s
        csv_lines = [
            'timestamp,event_type,value,unit,description'
        ]
        for event in cls.objects.all():
            line = [
                str(event.timestamp.timestamp()),
                event.event_type,
                clean_string(event.value),
                event.unit,
                clean_string(event.description),
            ]
            csv_lines.append(','.join(line))
        return '\n'.join(csv_lines)

class EventCalories(Event):
    UNITS = (
        ('kcal','Kilocalories'),
    )
    EVENT_TYPE = (
        ('calories','Calories'),
    )
    event_type = models.CharField(max_length=200, choices=EVENT_TYPE, default='calories')
    timestamp = models.DateTimeField(auto_now=True)
    unit = models.CharField(max_length=200, choices=UNITS, default='kcal')
    value = models.FloatField()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        logger.info(f'New calorie event: {self}')
        csv_path = AppSettings.get_key('events_calories_csv_path')
        csv_path = Path(csv_path)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(csv_path, 'w') as f:
            f.write(EventCalories.to_csv())
        logger.info(f'Updated calorie event CSV: {csv_path.absolute()}')

    # def clean(self):
    #     if self.timestamp.date() + timedelta(minutes=10) > datetime.now().date():
    #         raise ValidationError('Cannot add calorie events in the future', code='future_date')
    #     return super().clean()

class EventMedication(Event):
    MEDICATIONS = (
        ('novorapid','Novorapid'),
        ('medikinet','Medikinet'),
        ('ramidipin','RamiDipin'),
        ('atorvastatin','Atorvastatin'),
    )
    UNITS = (
        ('pill','Pill'),
        ('IE','Insulin Einheiten'),
        ('mg','Milligramm'),
    )
    EVENT_TYPE = (
        ('medication','Medication'),
    )
    event_type = models.CharField(max_length=200, choices=EVENT_TYPE, default='medication')
    unit = models.CharField(max_length=200, choices=UNITS, default='mg')
    value = models.FloatField()
    medication = models.CharField(max_length=200, choices=MEDICATIONS, default='medikinet')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        logger.info(f'New medication event: {self}')
        csv_path = AppSettings.get_key('events_medication_csv_path')
        csv_path = Path(csv_path)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(csv_path, 'w') as f:
            f.write(EventMedication.to_csv())
        logger.info(f'Updated medication event CSV: {csv_path.absolute()}')


    @classmethod
    def to_csv(cls):
        def clean_string(s):
            s = str(s)
            if ',' in s or '\n' in s:
                s = s.replace('"','""')
                s = '"' + s + '"'
            return s
        csv_lines = [
            'timestamp,event_type,medication,value,unit,description'
        ]
        for event in cls.objects.all():
            line = [
                str(event.timestamp.timestamp()),
                event.event_type,
                event.medication,
                clean_string(event.value),
                event.unit,
                clean_string(event.description),
            ]
            csv_lines.append(','.join(line))
        return '\n'.join(csv_lines)

    # validation
    def clean(self):
        if self.medication == 'novorapid' and self.unit != 'IE':
            raise ValidationError('Invalid unit for novorapid', code='unit_mismatch')
        if self.medication in {'medikinet','ramidipin','atorvastatin'} and self.unit not in {'pill','mg'}:
            raise ValidationError('Invalid unit for medication', code='unit_mismatch')
        if self.timestamp.date() + timedelta(minutes=10) > datetime.now(tz=gdtz()).date():
            raise ValidationError('Cannot add medication events in the future', code='future_date')
        return super().clean()

class EventExercise(Event):
    EXERCISES = (
        ('cardio','Cardio'),
        # Cycling
        ('strength','Strength'),
        # Pushups, Situps, Squats, Lifts
        ('flexibility','Flexibility'),
        # That thing where you touch your toes
    )
    UNITS = (
        ('minutes','Minutes'),
        ('km','Kilometers'),
        ('reps','Repetitions'),
    )
    EVENT_TYPE = (
        ('exercise','Exercise'),
    )
    event_type = models.CharField(max_length=200, choices=EVENT_TYPE, default='exercise')
    unit = models.CharField(max_length=200, choices=UNITS, default='minutes')
    value = models.FloatField()
    exercise = models.CharField(max_length=200, choices=EXERCISES, default='cardio')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        logger.info(f'New exercise event: {self}')
        csv_path = AppSettings.get_key('events_exercise_csv_path')
        csv_path = Path(csv_path)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(csv_path, 'w') as f:
            f.write(EventExercise.to_csv())
        logger.info(f'Updated exercise event CSV: {csv_path.absolute()}')
    
    @classmethod
    def to_csv(cls):
        def clean_string(s):
            s = str(s)
            if ',' in s or '\n' in s:
                s = s.replace('"','""')
                s = '"' + s + '"'
            return s
        csv_lines = [
            'timestamp,event_type,exercise,value,unit,description'
        ]
        for event in cls.objects.all():
            line = [
                str(event.timestamp.timestamp()),
                event.event_type,
                event.exercise,
                clean_string(event.value),
                event.unit,
                clean_string(event.description),
            ]
            csv_lines.append(','.join(line))
        return '\n'.join(csv_lines)
    
    def clean(self):
        if self.exercise == 'cardio' and self.unit != 'minutes':
            raise ValidationError('Invalid unit for cardio', code='unit_mismatch')
        if self.exercise in {'strength','flexibility'} and self.unit not in {'minutes','reps'}:
            raise ValidationError('Invalid unit for exercise', code='unit_mismatch')
        if self.timestamp.date() + timedelta(minutes=10) > datetime.now(tz=gdtz()).date():
            raise ValidationError('Cannot add exercise events in the future', code='future_date')
        return super().clean()

class EventPlantWatering(Event):
    PLANTS = (
        ('bambooLR','Bamboo (Living Room)'),
        ('bambooBR','Bamboo (Bedroom)'),
        ('fern','Fern'),
        ('pepperplant','Pepper Plant'),
        ('potato','Potato'),
        ('growbox','Grow Box'),
    )
    UNITS = (
        ('ml','Milliliters'),
        ('l','Liters'),
    )
    EVENT_TYPE = (
        ('plant_watering','Plant Watering'),
    )
    event_type = models.CharField(max_length=200, choices=EVENT_TYPE, default='plant_watering')
    unit = models.CharField(max_length=200, choices=UNITS, default='ml')
    value = models.FloatField()
    plant = models.CharField(max_length=200, choices=PLANTS, default='bambooLR')
    
    def clean(self):
        if self.timestamp.date() + timedelta(minutes=10) > datetime.now(tz=gdtz()).date():
            raise ValidationError('Cannot add plant watering events in the future', code='future_date')
        return super().clean()
