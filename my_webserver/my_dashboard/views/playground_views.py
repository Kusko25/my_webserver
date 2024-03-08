from django.views.generic import TemplateView, DetailView, FormView

from .utils import defaultContext

class PlaygroundView(TemplateView):
    template_name = 'my_dashboard/playground.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(defaultContext())
        return context