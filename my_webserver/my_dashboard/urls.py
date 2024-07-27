from django.urls import path
from .views import HomeView, MovieView, MedicationEventFormView, TVShowEpisodeView, PowerMonitorView
from .api.api_views import mark_show_favorite, mark_schedule_fulfilled_medication, mark_schedule_fulfilled_exercise, mark_schedule_fulfilled_plant
from .views.views_api import ErrorView_404, ControllerView_DailyTemp, PowerReadingView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('power_monitor/', PowerMonitorView.as_view(), name='power-monitor'),
    path('movies/<int:pk>/', MovieView.as_view(), name='movie'),
    path('tv_shows/episode/<int:pk>/', TVShowEpisodeView.as_view(), name='tv-show-episode'),
    path('events/register/medication/', MedicationEventFormView.as_view(), name='event-register-medication'),
    path('api/mark_show_favorite/<int:show_id>/', mark_show_favorite, name='mark-show-favorite'),
    path('api/medication/schedule/fulfill/<int:pk>/', mark_schedule_fulfilled_medication, name='mark-schedule-fulfilled'),
    path('api/medication/schedule/exercise/fulfill/<int:pk>/', mark_schedule_fulfilled_exercise, name='mark-schedule-fulfilled-exercise'),
    path('api/medication/schedule/plant/fulfill/<int:pk>/', mark_schedule_fulfilled_plant, name='mark-schedule-fulfilled-plant'),
    path('api/control/daily_temp/', ControllerView_DailyTemp.as_view(), name='control-daily-temp'),
    path('api/power_reading/', PowerReadingView.as_view(), name='power-reading'),
    
    # All 'api/' paths that weren't caught by the above paths will return a 404
    path('api/', ErrorView_404.as_view(), name='api-404'),
]