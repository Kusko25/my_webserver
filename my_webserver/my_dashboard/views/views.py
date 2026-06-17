from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView, DetailView, FormView
from django.shortcuts import render
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response

from ..models import AppSettings
from ..models import (
    Movie,
    MovieInstance,
    TVShowEpisodeInstance,
    TVShowEpisode,
    ScheduleMedication,
    ScheduleExercise,
    SchedulePlantWatering,
    EventCalories,
)
from ..logic import get_tv_schedule, parse_movie_feed
from ..forms import MedicationEventForm, CalorieEventForm, ExerciseEventForm

from .utils import defaultContext, get_context_topbar, sidebarItem
from ..variables import FRONTEND_TITLE_TEMPLATE

from datetime import date, timedelta
from logging import getLogger

logger = getLogger(__name__)

# Create your views here.

class SidebarMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Sidebar
        id_counter_dropdown = 0
        sidebar = dict()
        sidebar['title'] = 'Menu'
        nav_items = list()
        nav_items.append(sidebarItem(
                text='Admin', 
                icon='bi-archive', 
                href=reverse('admin:index')
        ))
        nav_items.append(sidebarItem(
                text='Home', 
                icon='bi-house', 
                href=reverse('home')
        ))
        nav_items.append(sidebarItem(
            text='Power Monitor',
            icon='bi-speedometer2',
            href=reverse('power-monitor')
        ))
        nav_items.append(sidebarItem(
            text='Gallery Viewer',
            icon='bi-images',
            href=reverse('gallery-viewer')
        ))
        id_counter_dropdown += 1
        sidebar['nav_items'] = nav_items
        context['sidebar'] = sidebar
        context = self.get_context_form_modals(context)
        return context
    
    def get_context_form_modals(self, context):
        modals:list = context.get("modals", [])
        modals.append(
            {
                "title": "Register Medication Event",
                "id": "modal-register-medication",
                "form": MedicationEventForm(),
                "icon": "bi bi-capsule",
                "action": reverse("api-form", args=["modal-register-medication"]),
                "skip_button": True,
            }
        )
        context["med_modal"] = modals[-1]
        
        modals.append(
            {
                "title": "Register Calories Event",
                "id": "modal-register-calories",
                "form": CalorieEventForm(),
                "icon": "bi bi-fire",
                "action": reverse("api-form", args=["modal-register-calories"]),
            }
        )
        modals.append(
            {
                "title": "Register Exercise Event",
                "id": "modal-register-exercise",
                "form": ExerciseEventForm(),
                "icon": "bi bi-lungs-fill",
                "action": reverse("api-form", args=["modal-register-exercise"]),
            }
        )
        
        context["modals"] = modals
        
        context["med_entries"] = [
            {
                "text" : "RamiDipin - 10mg",
                "link" : reverse("register-medication-event") + "?medication=ramidipin&unit=mg&amount=10",
            },
            {
                "text" : "Atorvastatin - 10mg",
                "link" : reverse("register-medication-event") + "?medication=atorvastatin&unit=mg&amount=10",
            },
            {
                "text" : "Medikinet - 10mg",
                "link" : reverse("register-medication-event") + "?medication=medikinet&unit=mg&amount=10",
            },
            {
                "text" : "Medikinet - 30mg",
                "link" : reverse("register-medication-event") + "?medication=medikinet&unit=mg&amount=30",
            },
        ]
        return context


class HomeView(SidebarMixin, TemplateView):
    template_name = "my_dashboard/dashboard.html"

    def get_context_tv_shows_pogdesign(self):
        context = dict()
        tv_shows = list()
        schedule = get_tv_schedule(ep_date=date.today())
        search_url = AppSettings.get_key("ddlvalley_search_url")
        if schedule is not None:
            for episode in schedule:
                tv_shows.append(
                    {
                        "show_name": episode.tv_show.title,
                        "episode_name": episode.title,
                        "episode_number": f"S{episode.season:02d}E{episode.episode:02d}",
                        "favorite": episode.tv_show.favorite,
                        "favorite_url": reverse(
                            "mark-show-favorite", args=[episode.tv_show.id]
                        ),
                        "search_url": search_url.format(
                            search_term="+".join(
                                f"{episode.tv_show.title} S{episode.season:02d}E{episode.episode:02d}".lower().split()
                            )
                        ),
                    }
                )
        context["tv_shows"] = tv_shows
        context["tv_shows"] = sorted(
            context["tv_shows"], key=lambda x: int(x["favorite"]), reverse=True
        )
        return context

    @staticmethod
    def get_context_tv_shows():
        context = dict()
        tv_shows = list()
        # parse_tv_feed(self.request)
        # Get last 30 days of episodes
        tv_show_insta_query = TVShowEpisodeInstance.objects.filter(
            date_added__gte=date.today() - timedelta(days=30)
        )
        episode_dict = dict()
        for instance in tv_show_insta_query:
            episode = instance.episode
            episode_dict[(episode.tv_show.title, episode.season, episode.episode)] = {
                "show_name": instance.episode.tv_show.title,
                "episode_name": instance.episode.title,
                "favorite": instance.episode.tv_show.favorite,
                "favorite_url": reverse(
                    "mark-show-favorite", args=[episode.tv_show.id]
                ),
                "episode_url": reverse("tv-show-episode", args=[episode.id]),
                "time_posted": instance.time_posted,
            }
        tv_shows = list(episode_dict.values())
        tv_shows = sorted(tv_shows, key=lambda x: x["time_posted"], reverse=True)[:10]
        tv_shows = sorted(tv_shows, key=lambda x: x["show_name"], reverse=True)
        for episode in tv_shows:
            if episode["time_posted"].date() == date.today():
                episode["time_posted"] = "Today " + episode["time_posted"].strftime(
                    "%H:%M"
                )
            else:
                episode["time_posted"] = episode["time_posted"].strftime(
                    "%Y-%m-%d %H:%M"
                )
        tv_shows = sorted(tv_shows, key=lambda x: int(x["favorite"]), reverse=True)
        context["tv_shows"] = tv_shows
        return context

    @staticmethod
    def get_context_medication():
        context = dict()
        medication_info = list()
        default_open = False
        for schedule in ScheduleMedication.objects.all():
            return_code, delta = schedule.is_satisfied()
            if return_code == ScheduleMedication.ReturnCodes.SATISFIED:
                medication_info.append(
                    {
                        "medication": schedule.get_medication_display(),
                        "variant": "table-success",
                        "message": "Satisfied",
                        "expected": f"{schedule.value} {schedule.get_unit_display()}",
                        "fulfilled": True,
                        "fulfill_link": None,
                    }
                )
            elif return_code == ScheduleMedication.ReturnCodes.NOT_SATISFIED:
                if delta:
                    message = f"Still missing {delta} {schedule.get_unit_display()}"
                else:
                    message = "Not satisfied"
                medication_info.append(
                    {
                        "medication": schedule.get_medication_display(),
                        "variant": "table-warning",
                        "message": message,
                        "expected": f"{schedule.value} {schedule.get_unit_display()}",
                        "fulfilled": False,
                        "fulfill_link": reverse(
                            "mark-schedule-fulfilled", args=[schedule.id]
                        ),
                    }
                )
                default_open = True
            elif return_code == ScheduleMedication.ReturnCodes.CANT_BE_DETERMINED:
                medication_info.append(
                    {
                        "medication": schedule.get_medication_display(),
                        "variant": "table-warning",
                        "message": "Can't be determined",
                        "expected": f"{schedule.value} {schedule.get_unit_display()}",
                        "fulfilled": True,
                        "fulfill_link": "#",
                    }
                )
                default_open = True
            elif return_code == ScheduleMedication.ReturnCodes.OVERSATISFIED:
                if delta:
                    message = f"Overdose by {delta} {schedule.get_unit_display()}"
                else:
                    message = "Overdose"
                medication_info.append(
                    {
                        "medication": schedule.get_medication_display(),
                        "variant": "table-danger",
                        "message": message,
                        "expected": f"{schedule.value} {schedule.get_unit_display()}",
                        "fulfilled": True,
                        "fulfill_link": None,
                    }
                )
                default_open = True
            elif return_code == ScheduleMedication.ReturnCodes.NOT_RELEVANT:
                continue
            else:
                raise Exception("Unknown return code")

        if len(medication_info) == 0:
            return context
        context["medication_info"] = medication_info
        return context, default_open

    @staticmethod
    def get_context_exercises():
        context = dict()
        exercises = list()
        default_open = False

        for schedule in ScheduleExercise.objects.all():
            return_code, delta = schedule.is_satisfied()
            if return_code == ScheduleExercise.ReturnCodes.SATISFIED:
                exercises.append(
                    {
                        "exercise": schedule.get_exercise_display(),
                        "variant": "table-success",
                        "message": "Satisfied",
                        "expected": f"{schedule.value} {schedule.get_unit_display()}",
                        "fulfilled": True,
                        "fulfill_link": reverse(
                            "mark-schedule-fulfilled-exercise", args=[schedule.id]
                        ),
                    }
                )
            elif return_code == ScheduleExercise.ReturnCodes.NOT_SATISFIED:
                if delta:
                    message = f"Still missing {delta} {schedule.get_unit_display()}"
                else:
                    message = "Not satisfied"
                exercises.append(
                    {
                        "exercise": schedule.get_exercise_display(),
                        "variant": "table-warning",
                        "message": message,
                        "expected": f"{schedule.value} {schedule.get_unit_display()}",
                        "fulfilled": False,
                        "fulfill_link": reverse(
                            "mark-schedule-fulfilled-exercise", args=[schedule.id]
                        ),
                    }
                )
                default_open = True
            elif return_code == ScheduleExercise.ReturnCodes.CANT_BE_DETERMINED:
                exercises.append(
                    {
                        "exercise": schedule.get_exercise_display(),
                        "variant": "table-warning",
                        "message": "Can't be determined",
                        "expected": f"{schedule.value} {schedule.get_unit_display()}",
                        "fulfilled": True,
                        "fulfill_link": reverse(
                            "mark-schedule-fulfilled-exercise", args=[schedule.id]
                        ),
                    }
                )
                default_open = True
            elif return_code == ScheduleExercise.ReturnCodes.OVERSATISFIED:
                if delta:
                    message = f"Oversatisfied by {delta} {schedule.get_unit_display()}"
                else:
                    message = "Oversatisfied"
                exercises.append(
                    {
                        "exercise": schedule.get_exercise_display(),
                        "variant": "table-success",
                        "message": message,
                        "expected": f"{schedule.value} {schedule.get_unit_display()}",
                        "fulfilled": True,
                        "fulfill_link": reverse(
                            "mark-schedule-fulfilled-exercise", args=[schedule.id]
                        ),
                    }
                )
            elif return_code == ScheduleExercise.ReturnCodes.NOT_RELEVANT:
                continue
            else:
                raise Exception(f"Unknown return code: {return_code}")

        if len(exercises) == 0:
            return context, default_open
        context["exercise_info"] = exercises
        return context, default_open

    def get_context_movies(self):
        context = dict()
        movies = dict()
        parse_movie_feed()
        cutoff_date = date.today() - timedelta(
            days=AppSettings.get_key("movies_time_delta")
        )
        movie_insta_query = MovieInstance.objects.filter(date_added__gte=cutoff_date)
        for movie_instance in movie_insta_query:
            if movie_instance.movie.title not in movies:
                movies[movie_instance.movie.title] = {
                    "name": movie_instance.movie.title,
                    "year": movie_instance.movie.release_year,
                    "href": reverse("movie", args=[movie_instance.movie.id]),
                    "resolutions": set(),
                    "groups": set(),
                }
            movies[movie_instance.movie.title]["resolutions"].add(
                movie_instance.resolution
            )
            movies[movie_instance.movie.title]["groups"].add(movie_instance.group)
        context["movies"] = list()
        for movie in movies.values():
            movie["resolutions"] = ", ".join(sorted(movie["resolutions"]))
            movie["groups"] = ", ".join(sorted(movie["groups"]))
            context["movies"].append(movie)
        return context

    @staticmethod
    def get_context_calories():
        context = dict()
        # Cut-off everything since 4am
        if timezone.now().hour < 4:
            dt_cutoff = timezone.now().replace(hour=4, minute=0, second=0, microsecond=0) - timedelta(days=1)
        else:
            dt_cutoff = timezone.now().replace(hour=4, minute=0, second=0, microsecond=0)
        context["cal_count"] = int(
            sum(
                x.value
                for x in EventCalories.objects.filter(timestamp__gte=dt_cutoff)
            )
        )
        context["cal_target"] = AppSettings.get_key("calories_target")
        
        if context["cal_count"] < context["cal_target"]*0.9:
            context["cal_level"] = "info"
        elif context["cal_count"] < context["cal_target"]*1.1:
            context["cal_level"] = "warning"
        else:
            context["cal_level"] = "danger"
        
        return {"calories": context}

    @staticmethod
    def get_context_plants():
        context = dict()
        plants = list()
        for schedule in SchedulePlantWatering.objects.all():
            return_code, delta = schedule.is_satisfied()
            if return_code == SchedulePlantWatering.ReturnCodes.SATISFIED:
                plants.append(
                    {
                        "plant": schedule.get_plant_display(),
                        "variant": "table-success",
                        "message": "Satisfied",
                        "expected": f"{schedule.value} {schedule.get_unit_display()}",
                        "fulfilled": True,
                        "fulfill_link": reverse(
                            "mark-schedule-fulfilled-plant", args=[schedule.id]
                        ),
                    }
                )
            elif return_code == SchedulePlantWatering.ReturnCodes.NOT_SATISFIED:
                if delta:
                    message = f"Still missing {delta} {schedule.get_unit_display()}"
                else:
                    message = "Not satisfied"
                plants.append(
                    {
                        "plant": schedule.get_plant_display(),
                        "variant": "table-warning",
                        "message": message,
                        "expected": f"{schedule.value} {schedule.get_unit_display()}",
                        "fulfilled": False,
                        "fulfill_link": reverse(
                            "mark-schedule-fulfilled-plant", args=[schedule.id]
                        ),
                    }
                )
            elif return_code == SchedulePlantWatering.ReturnCodes.CANT_BE_DETERMINED:
                plants.append(
                    {
                        "plant": schedule.get_plant_display(),
                        "variant": "table-warning",
                        "message": "Can't be determined",
                        "expected": f"{schedule.value} {schedule.get_unit_display()}",
                        "fulfilled": True,
                        "fulfill_link": reverse(
                            "mark-schedule-fulfilled-plant", args=[schedule.id]
                        ),
                    }
                )
            elif return_code == SchedulePlantWatering.ReturnCodes.OVERSATISFIED:
                if delta:
                    message = f"Oversatisfied by {delta} {schedule.get_unit_display()}"
                else:
                    message = "Oversatisfied"
                plants.append(
                    {
                        "plant": schedule.get_plant_display(),
                        "variant": "table-success",
                        "message": message,
                        "expected": f"{schedule.value} {schedule.get_unit_display()}",
                        "fulfilled": True,
                        "fulfill_link": reverse(
                            "mark-schedule-fulfilled-plant", args=[schedule.id]
                        ),
                    }
                )
            elif return_code == SchedulePlantWatering.ReturnCodes.NOT_RELEVANT:
                continue
            else:
                raise Exception(f"Unknown return code: {return_code}")
        if len(plants) == 0:
            return context
        context["plant_info"] = plants
        return context


    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(defaultContext())
        context.update(self.get_context_tv_shows())
        context.update(self.get_context_movies())
        context.update(self.get_context_plants())
        context.update(get_context_topbar())
        schedule_context, default_open = self.get_context_medication()
        context.update(schedule_context)
        exercise_context, tmp = self.get_context_exercises()
        context.update(exercise_context)

        context.update(self.get_context_calories())

        context["schedules_default_open"] = True
        return context

class APIViews:
    class FormView(APIView):
        def post(self, request, form_id):
            form = None
            if form_id == "modal-register-medication":
                form = MedicationEventForm(request.POST)
            elif form_id == "modal-register-calories":
                form = CalorieEventForm(request.POST)
            elif form_id == "modal-register-exercise":
                form = ExerciseEventForm(request.POST)
                
            if form is not None:
                if form.is_valid():
                    form.save()
                    return Response(
                        {'message':'success'},
                        status=200
                    )
                else:
                    return Response(
                        render(request, "my_dashboard/components/render_form.html", {"form": form}),
                        status=400
                    )
            else:
                return Response(
                    {'message':'invalid form id'},
                    status=400
                )
    
    def schedulesView(request):
        context = dict()
        context.update(HomeView.get_context_plants())
        schedule_context, _ = HomeView.get_context_medication()
        context.update(schedule_context)
        exercise_context, _ = HomeView.get_context_exercises()
        context.update(exercise_context)
        context["schedules_default_open"] = True
        return render(request, "my_dashboard/components/schedules.html", context)

    def tvShowView(request):
        context = HomeView.get_context_tv_shows()
        return render(request, "my_dashboard/components/tv_shows.html", context)

    def caloriesView(request):
        try:
            change = float(request.GET["calories"])
            EventCalories.objects.create(value=change)
        except (KeyError, ValueError):
            pass
        
        context = HomeView.get_context_calories()
        return render(request, "my_dashboard/components/topbar_calorie_count.html", context)

class PowerMonitorView(TemplateView):
    template_name = "my_dashboard/power_monitor.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(defaultContext())
        context.update(get_context_topbar())
        context["page_heading"] = "Power Monitor"
        context["title"] = FRONTEND_TITLE_TEMPLATE % "Power Monitor"
        return context

class MovieView(DetailView):
    model = Movie
    template_name = "my_dashboard/model_movies.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(defaultContext(active_item=self.object.title))
        context["page_heading"] = self.object.title
        context["movie_instances"] = [
            {
                "resolution": inst.resolution,
                "group": inst.group,
                "url": inst.url,
                "date_added": inst.date_added.strftime("%Y-%m-%d"),
            }
            for inst in MovieInstance.objects.filter(movie=self.object)
        ]
        return context

class TVShowEpisodeView(DetailView):
    model = TVShowEpisode
    template_name = "my_dashboard/model_episode.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(defaultContext(active_item=self.object.title))
        context["page_heading"] = self.object.tv_show.title
        context["subtitle"] = self.object.title
        context["episode_instances"] = [
            {
                "title": inst.episode.title,
                "resolution": inst.resolution,
                "source": inst.source,
                "group": inst.group,
                "url": inst.url,
                "date_added": inst.date_added.strftime("%Y-%m-%d"),
                "time_posted": inst.time_posted.strftime("%Y-%m-%d %H:%M"),
            }
            for inst in TVShowEpisodeInstance.objects.filter(episode=self.object)
        ]
        return context

class MedicationEventFormView(FormView):
    template_name = "my_dashboard/register_event.html"
    form_class = MedicationEventForm
    success_url = reverse_lazy("event-register-medication")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(defaultContext())
        context["event_type"] = "medication"
        context["page_heading"] = "Register Medication Event"
        return context

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

class ExperimentView(TemplateView):
    template_name = "my_dashboard/experiment.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(defaultContext())
        context["page_heading"] = "Experiment"
        return context