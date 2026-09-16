import json
import logging
from datetime import date, datetime, timedelta

from django.db import models
from django.utils import timezone
from django.utils.timezone import get_default_timezone as gdtz

from my_dashboard.utils import utils

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
            'events_exercise_csv_path': ('outputs/events/exercise.csv', 'str'),
            'events_calories_csv_path': ('outputs/events/calories.csv', 'str'),
            'ddlvalley_search_url': ('https://www.ddlvalley.me/?s={search_term}', 'str'),
            'tvshows_last_update': (timezone.now() - timedelta(days=7), 'datetime'),
            'tv_filters': ([], 'json'),
            'tv_feed_url': ('https://www.ddlvalley.me/category/tv-shows/feed/', 'str'),
            'tv_time_delta': (24, 'int'),
            'calories_target': (2200, 'int'),
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
                AppSettings.objects.create(
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
        if value_type is None:
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
        AppSettings.objects.create(
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

    @classmethod
    def get_key(cls, key:str, profile='default'):
        return cls.c_objects.get(key=key, profile=profile)
    
    @classmethod
    def set_key(cls, key:str, value, value_type=None, profile='default'):
        cls.c_objects.set(key, value, value_type, profile)


    def __str__(self):
        return self.key
    
    def display_value(self):
        return self.value[:50]
    display_value.short_description = 'Value' # type: ignore

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
    
    @classmethod
    def make_new(cls, **kwargs):
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
            kwargs['air_date'] = datetime.strptime(kwargs['air_date'], pogdesign_format).astimezone(tz=gdtz()).date()

        
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
