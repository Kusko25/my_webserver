from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView, DetailView, FormView
from django.utils import timezone

from ..models import AppSettings
from ..models import Movie, MovieInstance, TVShowEpisodeInstance, TVShowEpisode, ScheduleMedication, ScheduleExercise
from ..logic import get_tv_schedule, parse_movie_feed, parse_tv_feed
from ..forms import MedicationEventForm

from .utils import defaultContext

from datetime import date, timedelta

# Create your views here.

class HomeView(TemplateView):
    template_name = 'my_dashboard/dashboard.html'

    def get_context_tv_shows_pogdesign(self):
        context = dict()
        tv_shows = list()
        schedule = get_tv_schedule(ep_date=date.today())
        search_url = AppSettings.get_key('ddlvalley_search_url')
        if schedule!=None:
            for episode in schedule:
                tv_shows.append(
                    {
                        'show_name': episode.tv_show.title,
                        'episode_name': episode.title,
                        'episode_number': f'S{episode.season:02d}E{episode.episode:02d}',
                        'favorite': episode.tv_show.favorite,
                        'favorite_url': reverse('mark-show-favorite', args=[episode.tv_show.id]),
                        'search_url': search_url.format(search_term="+".join(f'{episode.tv_show.title} S{episode.season:02d}E{episode.episode:02d}'.lower().split()))
                    }
                )
        context['tv_shows'] = tv_shows
        context['tv_shows'] = sorted(context['tv_shows'], key=lambda x: int(x['favorite']), reverse=True)
        return context
    
    def get_context_tv_shows(self):
        context = dict()
        tv_shows = list()
        parse_tv_feed(self.request)
        # Get TV show Episodes that were added in the last x hours
        cutoff_date = date.today() - timedelta(hours=AppSettings.get_key('tv_time_delta'))
        tv_show_insta_query = TVShowEpisodeInstance.objects.filter(time_posted__gte=cutoff_date)
        episode_set = set()
        for instance in tv_show_insta_query:
            episode = instance.episode
            if f'{instance.episode.tv_show.title} S{episode.season:02d}E{episode.episode:02d}' in episode_set:
                continue
            tv_shows.append(
                {
                    'show_name': instance.episode.tv_show.title,
                    'episode_name': instance.episode.title,
                    'favorite': instance.episode.tv_show.favorite,
                    'favorite_url': reverse('mark-show-favorite', args=[episode.tv_show.id]),
                    'episode_url': reverse('tv-show-episode', args=[episode.id]),
                }
            )
            episode_set.add(f'{episode.tv_show.title} S{episode.season:02d}E{episode.episode:02d}')
        tv_shows = sorted(tv_shows, key=lambda x: x['show_name'], reverse=True)
        tv_shows = sorted(tv_shows, key=lambda x: int(x['favorite']), reverse=True)
        context['tv_shows'] = tv_shows
        return context

    def get_context_medication(self):
        context = dict()
        medication_info = list()
        default_open = False
        for schedule in ScheduleMedication.objects.all():
            return_code, delta = schedule.is_satisfied()
            if return_code == ScheduleMedication.ReturnCodes.SATISFIED:
                medication_info.append({
                    'medication': schedule.get_medication_display(),
                    'variant': 'table-success',
                    'message': 'Satisfied',
                    'expected': f'{schedule.value} {schedule.get_unit_display()}',
                    'fulfilled': True,
                    'fulfill_link': None
                })
            elif return_code == ScheduleMedication.ReturnCodes.NOT_SATISFIED:
                if delta:
                    message = f'Still missing {delta} {schedule.get_unit_display()}'
                else:
                    message = 'Not satisfied'
                medication_info.append({
                    'medication': schedule.get_medication_display(),
                    'variant': 'table-warning',
                    'message': message,
                    'expected': f'{schedule.value} {schedule.get_unit_display()}',
                    'fulfilled': False,
                    'fulfill_link': reverse('mark-schedule-fulfilled', args=[schedule.id])
                })
                default_open = True
            elif return_code == ScheduleMedication.ReturnCodes.CANT_BE_DETERMINED:
                medication_info.append({
                    'medication': schedule.get_medication_display(),
                    'variant': 'table-warning',
                    'message': 'Can\'t be determined',
                    'expected': f'{schedule.value} {schedule.get_unit_display()}',
                    'fulfilled': True,
                    'fulfill_link': '#'
                })
                default_open = True
            elif return_code == ScheduleMedication.ReturnCodes.OVERSATISFIED:
                if delta:
                    message = f'Overdose by {delta} {schedule.get_unit_display()}'
                else:
                    message = 'Overdose'
                medication_info.append({
                    'medication': schedule.get_medication_display(),
                    'variant': 'table-danger',
                    'message': message,
                    'expected': f'{schedule.value} {schedule.get_unit_display()}',
                    'fulfilled': True,
                    'fulfill_link': None
                })
                default_open = True
            elif return_code == ScheduleMedication.ReturnCodes.NOT_RELEVANT:
                continue
            else:
                raise Exception('Unknown return code')
        
        if len(medication_info) == 0:
            return context
        context['medication_info'] = medication_info
        return context, default_open
    
    def get_context_exercises(self):
        context = dict()
        exercises = list()
        default_open = False

        for schedule in ScheduleExercise.objects.all():
            return_code, delta = schedule.is_satisfied()
            if return_code == ScheduleExercise.ReturnCodes.SATISFIED:
                exercises.append({
                    'exercise': schedule.get_exercise_display(),
                    'variant': 'table-success',
                    'message': 'Satisfied',
                    'expected': f'{schedule.value} {schedule.get_unit_display()}',
                    'fulfilled': True,
                    'fulfill_link': reverse('mark-schedule-fulfilled-exercise', args=[schedule.id])
                })
            elif return_code == ScheduleExercise.ReturnCodes.NOT_SATISFIED:
                if delta:
                    message = f'Still missing {delta} {schedule.get_unit_display()}'
                else:
                    message = 'Not satisfied'
                exercises.append({
                    'exercise': schedule.get_exercise_display(),
                    'variant': 'table-warning',
                    'message': message,
                    'expected': f'{schedule.value} {schedule.get_unit_display()}',
                    'fulfilled': False,
                    'fulfill_link': reverse('mark-schedule-fulfilled-exercise', args=[schedule.id])
                })
                default_open = True
            elif return_code == ScheduleExercise.ReturnCodes.CANT_BE_DETERMINED:
                exercises.append({
                    'exercise': schedule.get_exercise_display(),
                    'variant': 'table-warning',
                    'message': 'Can\'t be determined',
                    'expected': f'{schedule.value} {schedule.get_unit_display()}',
                    'fulfilled': True,
                    'fulfill_link': reverse('mark-schedule-fulfilled-exercise', args=[schedule.id])
                })
                default_open = True
            elif return_code == ScheduleExercise.ReturnCodes.OVERSATISFIED:
                if delta:
                    message = f'Oversatisfied by {delta} {schedule.get_unit_display()}'
                else:
                    message = 'Oversatisfied'
                exercises.append({
                    'exercise': schedule.get_exercise_display(),
                    'variant': 'table-success',
                    'message': message,
                    'expected': f'{schedule.value} {schedule.get_unit_display()}',
                    'fulfilled': True,
                    'fulfill_link': reverse('mark-schedule-fulfilled-exercise', args=[schedule.id])
                })
            elif return_code == ScheduleExercise.ReturnCodes.NOT_RELEVANT:
                continue
            else:
                raise Exception(f'Unknown return code: {return_code}')
            
        if len(exercises) == 0:
            return context, default_open
        context['exercise_info'] = exercises
        return context, default_open

    def get_context_movies(self):
        context = dict()
        movies = dict()
        parse_movie_feed()
        cutoff_date = date.today() - timedelta(days=AppSettings.get_key('movies_time_delta'))
        movie_insta_query = MovieInstance.objects.filter(date_added__gte=cutoff_date)
        for movie_instance in movie_insta_query:
            if movie_instance.movie.title not in movies:
                movies[movie_instance.movie.title] = {
                    'name': movie_instance.movie.title,
                    'year': movie_instance.movie.release_year,
                    'href': reverse('movie', args=[movie_instance.movie.id]), 
                    'resolutions': set(),
                    'groups': set()
                }
            movies[movie_instance.movie.title]['resolutions'].add(movie_instance.resolution)
            movies[movie_instance.movie.title]['groups'].add(movie_instance.group)
        context['movies'] = list()
        for movie in movies.values():
            movie['resolutions'] = ', '.join(sorted(movie['resolutions']))
            movie['groups'] = ', '.join(sorted(movie['groups']))
            context['movies'].append(movie)
        return context


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(defaultContext())
        context.update(self.get_context_tv_shows())
        context.update(self.get_context_movies())
        schedule_context, default_open = self.get_context_medication()
        context.update(schedule_context)
        exercise_context, tmp = self.get_context_exercises()
        default_open = default_open or tmp
        context.update(exercise_context)

        context['schedules_default_open'] = default_open
        return context

class MovieView(DetailView):
    model = Movie
    template_name = 'my_dashboard/model_movies.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(defaultContext(active_item=self.object.title))
        context['page_heading'] = self.object.title
        context['movie_instances'] = [{
            'resolution': inst.resolution,
            'group': inst.group,
            'url': inst.url,
            'date_added': inst.date_added.strftime('%Y-%m-%d')
            }
            for inst in MovieInstance.objects.filter(movie=self.object)]
        return context

class TVShowEpisodeView(DetailView):
    model = TVShowEpisode
    template_name = 'my_dashboard/model_episode.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(defaultContext(active_item=self.object.title))
        context['page_heading'] = self.object.tv_show.title
        context['subtitle'] = self.object.title
        context['episode_instances'] = [{
            'title': inst.episode.title,
            'resolution': inst.resolution,
            'source': inst.source,
            'group': inst.group,
            'url': inst.url,
            'date_added': inst.date_added.strftime('%Y-%m-%d'),
            'time_posted': inst.time_posted.strftime('%Y-%m-%d %H:%M')
            }
            for inst in TVShowEpisodeInstance.objects.filter(episode=self.object)]
        return context

class MedicationEventFormView(FormView):
    template_name = 'my_dashboard/register_event.html'
    form_class = MedicationEventForm
    success_url = reverse_lazy('event-register-medication')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(defaultContext())
        context['event_type'] = 'medication'
        context['page_heading'] = 'Register Medication Event'
        return context

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)