from .models import Course

from django.views import generic

class CourseList(generic.ListView):
    template_name = 'graph/index.html'
    context_object_name = 'nom_list'
    paginate_by = 50  # Si vous voulez la pagination

    def get_queryset(self):
        """Return all finishers, ordered by their finish time."""
        return Course.objects.all().order_by('nom').distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object_list:
            context['field_names'] = [field.verbose_name for field in self.object_list[0]._meta.fields]
        return context
