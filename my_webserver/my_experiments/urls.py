from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('hello-webpack/', TemplateView.as_view(template_name='hello_webpack.html')),
]