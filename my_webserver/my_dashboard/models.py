from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

from . import utils

from datetime import datetime, date, timedelta
from pathlib import Path
import logging, json, enum


logger = logging.getLogger(__name__)

class AppSettingsManager(models.Manager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.defaults = {
            'movies_feed_url': ("https://www.ddlvalley.me/category/movies/feed/",'str'),
            'movies_last_update': (timezone.now() - timedelta(days=7), 'datetime'),
            'movies_filters': (['cam'], 'json'),
            'movies_time_delta': (3, 'int'),
            'events_medication_csv_path': ('outputs/events/medication.csv', 'str'),
            'ddlvalley_search_url': ('https://www.ddlvalley.me/?s={search_term}', 'str'),
            'tvshows_last_update': (timezone.now() - timedelta(days=7), 'datetime'),
            'tv_filters': ([], 'json'),
            'tv_feed_url': ('https://www.ddlvalley.me/category/tv-shows/feed/', 'str'),
            'tv_time_delta': (24, 'int'),
        }
        # For getting from db
        self.typecast = {
            'str': str,
            'int': int,
            'bool': lambda x: x=="True",
            'date': date.fromisoformat,
            'datetime': datetime.fromisoformat,
            'json': json.loads,
        }

        # For saving to db
        self.typecast_rev = {
            'str': lambda x: x,
            'int': str,
            'bool': str,
            'date': lambda x: x.isoformat(),
            'datetime': lambda x: x.isoformat(),
            'json': json.dumps,
        }

        self.infer_type = {
            str: 'str',
            int: 'int',
            bool: 'bool',
            date: 'date',
            datetime: 'datetime',
            list: 'json',
            dict: 'json',
        }
        
        # Typecast the defaults
        self.defaults = {
            key: (self.typecast_rev[value[1]](value[0]), value[1]) for key, value in self.defaults.items()
        }
    
    def get_queryset(self) -> models.QuerySet:
        prev_set_objects = super().get_queryset()

        added_keys = False
        for key, value in self.defaults.items():
            if not prev_set_objects.filter(key=key).exists():
                setting = AppSettings.objects.create(
                    key=key, 
                    value=value[0], 
                    value_type=value[1], 
                    profile='default'
                )
                added_keys = True
        if added_keys:
            prev_set_objects = super().get_queryset()
        return prev_set_objects
    
    def get(self, key, profile='default'):
        try:
            setting = AppSettings.objects.get(key=key, profile=profile)
            return self.typecast[setting.value_type](setting.value)
        except AppSettings.DoesNotExist:
            setting =  AppSettings.objects.create(
                key=key, 
                value=self.defaults[key][0], 
                value_type=self.defaults[key][1], 
                profile=profile
            )
            return self.typecast[setting.value_type](setting.value)
        
    def set(self, key, value, value_type=None, profile='default'):
        if value_type==None:
            if type(value) not in self.infer_type:
                raise ValueError(f'Could not infer value_type from value: {value}')
            value_type = self.infer_type[type(value)]

        if value_type not in self.typecast:
            raise ValueError(f'Invalid value_type: {value_type}')
        
        # clear key
        AppSettings.objects.filter(key=key, profile=profile).delete()

        # typecast value
        value = self.typecast_rev[value_type](value)
        # set key
        setting = AppSettings.objects.create(
            key=key,
            value=value,
            value_type=value_type,
            profile=profile
        ).save()

class AppSettings(models.Model):
    key = models.CharField(max_length=200, unique=True)
    value = models.TextField()
    value_type = models.CharField(max_length=200, default='str', choices=(
        ('str','String'),
        ('int','Integer'),
        ('bool','Boolean'),
        ('date','Date'),
        ('datetime','DateTime'),
        ('json','JSON'),
    ))

    # Not used yet, but if then the combination of key and profile should be unique
    profile = models.CharField(max_length=200, default='default')

    objects = models.Manager()
    c_objects = AppSettingsManager()

    def get_key(key, profile='default'):
        return AppSettings.c_objects.get(key=key, profile=profile)
    
    def set_key(key, value, value_type=None, profile='default'):
        AppSettings.c_objects.set(key, value, value_type, profile)


    def __str__(self):
        return self.key
    
    def display_value(self):
        return self.value[:50]
    display_value.short_description = 'Value'

    class Meta:
        verbose_name = "App Setting"
        verbose_name_plural = "App Settings"

# Create your models here.
class TVShow(models.Model):
    title = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    favorite = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class TVShowEpisode(models.Model):
    title = models.CharField(max_length=200)
    season = models.IntegerField()
    episode = models.IntegerField()
    air_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    tv_show = models.ForeignKey(TVShow, on_delete=models.CASCADE)

    def make_new(**kwargs):
        save = kwargs.pop('save',True)

        show_name = kwargs.pop('tv_show','DefaultShow')
        if not isinstance(show_name, TVShow):
            show_name = utils.process_show_name(show_name)

        if 'season' in kwargs and isinstance(kwargs['season'], str):
            kwargs['season'] = int(kwargs['season'])
        if 'episode' in kwargs and isinstance(kwargs['episode'], str):
            kwargs['episode'] = int(kwargs['episode'])
        if 'air_date' in kwargs and isinstance(kwargs['air_date'], str):
            pogdesign_format = "" # TODO: Add pogdesign format
            kwargs['air_date'] = datetime.strptime(kwargs['air_date'], pogdesign_format).date()

        
        if not isinstance(show_name, TVShow):
            show, created = TVShow.objects.get_or_create(title=show_name)
            if created:
                logger.info(f'Created new TV show: {show}')
        
        kwargs['tv_show'] = show_name
        episode = TVShowEpisode(**kwargs)
        if save:
            episode.save()
        return episode
    
    def __str__(self):
        repr = f"{self.tv_show} - S{self.season:02d}E{self.episode:02d}"
        if self.title:
            repr += f" - {self.title}"
        return repr

class TVShowEpisodeInstance(models.Model):
    episode = models.ForeignKey(TVShowEpisode, on_delete=models.CASCADE)
    resolution = models.CharField(max_length=50, default='Unknown')
    source = models.CharField(max_length=50, default='Unknown')
    group = models.CharField(max_length=50, default='Unknown')
    url = models.URLField(max_length=200)
    date_added = models.DateField(auto_now_add=True)
    time_posted = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'{self.episode} - {self.resolution}'

class Movie(models.Model):
    title = models.CharField(max_length=200)
    release_year = models.IntegerField(default=0)

    def __str__(self):
        return self.title

class MovieInstance(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    resolution = models.CharField(max_length=50, default='Unknown')
    group = models.CharField(max_length=50, default='Unknown')
    url = models.URLField(max_length=200)
    date_added = models.DateField(auto_now_add=True)

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

    def to_csv():
        def clean_string(s):
            s = str(s)
            if ',' in s or '\n' in s:
                s = s.replace('"','""')
                s = '"' + s + '"'
            return s
        csv_lines = [
            'timestamp,event_type,value,unit,description'
        ]
        for event in Event.objects.all():
            line = [
                str(event.timestamp.timestamp()),
                event.event_type,
                clean_string(event.value),
                event.unit,
                clean_string(event.description),
            ]
            csv_lines.append(','.join(line))
        return '\n'.join(csv_lines)

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


    def to_csv():
        def clean_string(s):
            s = str(s)
            if ',' in s or '\n' in s:
                s = s.replace('"','""')
                s = '"' + s + '"'
            return s
        csv_lines = [
            'timestamp,event_type,medication,value,unit,description'
        ]
        for event in EventMedication.objects.all():
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
        if self.timestamp.date() + timedelta(minutes=10) > datetime.now().date():
            raise ValidationError('Cannot add medication events in the future', code='future_date')
        return super().clean()

class MedicationSchedule(models.Model):
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
                return f'{self.medication} - {self.method} - {", ".join([datetime.fromisoformat(str(day)).strftime("%A") for day in self.weekdays])}'
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
                return MedicationSchedule.ReturnCodes.NOT_RELEVANT, None
            
        if sum_matching == self.value:
            if len(matching_units) == len(events):
                return MedicationSchedule.ReturnCodes.SATISFIED, None
            else:
                return MedicationSchedule.ReturnCodes.OVERSATISFIED, None
        elif sum_matching < self.value:
            if len(matching_units) == len(events):
                return MedicationSchedule.ReturnCodes.NOT_SATISFIED, self.value - sum_matching
            else:
                return MedicationSchedule.ReturnCodes.CANT_BE_DETERMINED, None
        else:
            if len(matching_units) == len(events):
                return MedicationSchedule.ReturnCodes.OVERSATISFIED, sum_matching - self.value
            else:
                return MedicationSchedule.ReturnCodes.OVERSATISFIED, None
