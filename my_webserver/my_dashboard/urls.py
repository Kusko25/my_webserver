from django.urls import path

from .api.api_views import (
    mark_schedule_fulfilled_exercise,
    mark_schedule_fulfilled_medication,
    mark_schedule_fulfilled_plant,
    mark_show_favorite,
    register_medication_event,
)
from .api.weather import WeatherInfoView
from .views import (
    APIViews,
    ExperimentView,
    GalleryView,
    GalleryViewerAPI,
    HomeView,
    MedicationEventFormView,
    MovieView,
    PowerMonitorView,
    TVShowEpisodeView,
)
from .views.rss.read_comics_online import StarTrekLowerDecks2024
from .views.views_api import (
    ControllerView_DailyTemp,
    ControlMonitorView,
    ErrorView_404,
    PowerReadingView,
    RefreshFeedsView,
    RefreshGadgetView,
)

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("power_monitor/", PowerMonitorView.as_view(), name="power-monitor"),
    path("gallery_viewer/", GalleryView.as_view(), name="gallery-viewer"),
    path("movies/<int:pk>/", MovieView.as_view(), name="movie"),
    path(
        "tv_shows/episode/<int:pk>/",
        TVShowEpisodeView.as_view(),
        name="tv-show-episode",
    ),
    path(
        "events/register/medication/",
        MedicationEventFormView.as_view(),
        name="event-register-medication",
    ),
    path("experiment/", ExperimentView.as_view(), name="experiment"),
]
# api paths
urlpatterns += [
    path("api/gallery/parse/", GalleryViewerAPI.as_view(), name="gallery-parse"),
    path(
        "api/mark_show_favorite/<int:show_id>/",
        mark_show_favorite,
        name="mark-show-favorite",
    ),
    path(
        "api/medication/event/register/",
        register_medication_event,
        name="register-medication-event",
    ),
    path(
        "api/medication/schedule/fulfill/<int:pk>/",
        mark_schedule_fulfilled_medication,
        name="mark-schedule-fulfilled",
    ),
    path(
        "api/medication/schedule/exercise/fulfill/<int:pk>/",
        mark_schedule_fulfilled_exercise,
        name="mark-schedule-fulfilled-exercise",
    ),
    path(
        "api/medication/schedule/plant/fulfill/<int:pk>/",
        mark_schedule_fulfilled_plant,
        name="mark-schedule-fulfilled-plant",
    ),
    path(
        "api/control/daily_temp/",
        ControllerView_DailyTemp.as_view(),
        name="control-daily-temp",
    ),
    path("api/power_reading/", PowerReadingView.as_view(), name="power-reading"),
    path("api/monitor_control/", ControlMonitorView.as_view(), name="monitor-control"),
    path("api/update_rss/", RefreshFeedsView.as_view(), name="update-rss"),
    path("api/gadget_data/", RefreshGadgetView.as_view(), name="gadget-data"),
    path("api/gadget/weather/", WeatherInfoView.as_view(), name="gadget-weather"),
    path("api/html/component/tv-shows/", APIViews.tvShowView, name="comp-tv-shows"),
    path("api/html/component/schedules/", APIViews.schedulesView, name="comp-schedules"),
    path("api/html/component/calories/", APIViews.caloriesView, name="comp-calories"),
    path("api/form/<str:form_id>/", APIViews.FormView.as_view(), name="api-form"),
    # All 'api/' paths that weren't caught by the above paths will return a 404
    path("api/", ErrorView_404.as_view(), name="api-404"),
]
# rss paths
urlpatterns += [
    # http://127.0.0.1:5000/rss/star-trek-lower-decks-2024
    path("rss/star-trek-lower-decks-2024/", StarTrekLowerDecks2024.view, name="rss-star-trek-lower-decks-2024"),
]
