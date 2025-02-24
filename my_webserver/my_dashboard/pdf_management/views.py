from django.views.generic import TemplateView, DetailView, FormView, View
import my_dashboard.pdf_management.models as models
import my_dashboard.pdf_management.file_management as file_management

class BaseContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class InboxView(BaseContextMixin, TemplateView):
    template_name = 'pdf_management/inbox.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['new_files'] = models.NewFile.get_new_files()
        return context

class NewFileDetailView(BaseContextMixin, DetailView):
    model = models.NewFile
    template_name = 'pdf_management/new_file.html'
    context_object_name = 'new_file'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = models.Category.objects.all()
        return context

class NewFileFormView(BaseContextMixin, FormView):
    template_name = 'pdf_management/new_file_form.html'
    
    def get_form_class(self):
        form_name = models.Category.objects.get(slug=self.kwargs['category']).form_class
        # return getattr(forms, form_name) # Uncomment when forms are implemented

class ListDocumentsView(BaseContextMixin, TemplateView):
    template_name = 'pdf_management/list_documents.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documents'] = models.Document.objects.all()
        return context