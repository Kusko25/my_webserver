from django.urls import path
from .views import HomeView, MovieView, MedicationEventFormView, TVShowEpisodeView
from .api.api_views import mark_show_favorite

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('movies/<int:pk>/', MovieView.as_view(), name='movie'),
    path('tv_shows/episode/<int:pk>/', TVShowEpisodeView.as_view(), name='tv-show-episode'),
    path('events/register/medication/', MedicationEventFormView.as_view(), name='event-register-medication'),
    path('api/mark_show_favorite/<int:show_id>/', mark_show_favorite, name='mark-show-favorite')
]