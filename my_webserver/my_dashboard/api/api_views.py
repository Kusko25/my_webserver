from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages

from ..models import TVShow, ScheduleMedication, ScheduleExercise, SchedulePlantWatering, EventMedication

import logging

logger = logging.getLogger(__name__)

def mark_show_favorite(request, show_id):
    """Mark a TVShow as a favorite.
    This marks a TVShow as a favorite and redirects to the dashboard.
    TODO: Make it instead return a JSON response and use AJAX to update the UI.
    Also learn what AJAX is.
    """
    show = TVShow.objects.filter(id=show_id)
    if len(show) == 0:
        logger.error(f'No TVShow with id {show_id} found')
        return HttpResponseRedirect(reverse('home'))
    show = show[0]
    show.favorite = not show.favorite
    show.save()
    return HttpResponseRedirect(reverse('home'))

def mark_schedule_fulfilled_medication(request, pk):
    """Mark a MedicationSchedule as fulfilled."""
    schedule = ScheduleMedication.objects.get(pk=pk)
    schedule.fulfill()
    return HttpResponseRedirect(reverse('home'))

def mark_schedule_fulfilled_exercise(request, pk):
    """Mark a MedicationSchedule as fulfilled."""
    schedule = ScheduleExercise.objects.get(pk=pk)
    schedule.fulfill()
    return HttpResponseRedirect(reverse('home'))

def mark_schedule_fulfilled_plant(request, pk):
    """Mark a MedicationSchedule as fulfilled."""
    schedule = SchedulePlantWatering.objects.get(pk=pk)
    schedule.fulfill()
    return HttpResponseRedirect(reverse('home'))

def register_medication_event(request):
    """Register a medication event."""
    medication = request.GET.get('medication')
    unit = request.GET.get('unit')
    amount = request.GET.get('amount')
    time = timezone.now()
    
    try:
        amount = float(amount)
    except ValueError:
        logger.error('Invalid amount')
        messages.error(request, 'Invalid amount')
        return HttpResponseRedirect(reverse('home'))
    
    if not all([medication, unit, amount]):
        logger.error('Missing parameters')
        messages.error(request, 'Missing parameters')
        return HttpResponseRedirect(reverse('home'))
    
    event = EventMedication(
        medication=medication,
        unit=unit,
        value=amount,
        timestamp=time,
    )
    
    try:
        event.save()
    except Exception as e:
        logger.error(f'Error saving event: {e}')
        messages.error(request, 'Error saving event')
        return HttpResponseRedirect(reverse('home'))
    return HttpResponseRedirect(reverse('home'))