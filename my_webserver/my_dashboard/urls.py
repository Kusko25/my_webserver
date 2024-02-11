from django.urls import path,include
from .views import HomeView, MovieView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('movies/<int:pk>/', MovieView.as_view(), name='movie'),
]