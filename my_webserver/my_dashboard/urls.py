from django.urls import path
from .views import HomeView, MovieView, MedicationEventFormView, TVShowEpisodeView
from .api.api_views import mark_show_favorite, mark_schedule_fulfilled_medication, mark_schedule_fulfilled_exercise

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('movies/<int:pk>/', MovieView.as_view(), name='movie'),
    path('tv_shows/episode/<int:pk>/', TVShowEpisodeView.as_view(), name='tv-show-episode'),
    path('events/register/medication/', MedicationEventFormView.as_view(), name='event-register-medication'),
    path('api/mark_show_favorite/<int:show_id>/', mark_show_favorite, name='mark-show-favorite'),
    path('api/medication/schedule/fulfill/<int:pk>/', mark_schedule_fulfilled_medication, name='mark-schedule-fulfilled'),
    path('api/medication/schedule/exercise/fulfill/<int:pk>/', mark_schedule_fulfilled_exercise, name='mark-schedule-fulfilled-exercise'),
]