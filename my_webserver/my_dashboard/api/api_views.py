from django.http import HttpResponseRedirect
from django.urls import reverse

from rest_framework import status
from ..models import TVShow

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