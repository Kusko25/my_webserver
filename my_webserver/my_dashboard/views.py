from django.shortcuts import render
from django.urls import reverse
from django.views.generic import TemplateView, DetailView

from .models import AppSettings
from .models import TVShow, TVShowEpisode, Movie, MovieInstance
from .logic import get_tv_schedule, parse_movie_feed

from datetime import datetime, date, timedelta
from collections import defaultdict

# Create your views here.
def sidebarItem(text='', icon=None, href=None, dropdown_list=None, dropdown_id=None, active=False):
    item = dict()
    item['text'] = text
    if icon!=None:
        item['icon'] = icon
    if href!=None:
        item['href'] = href
    if dropdown_list!=None:
        item['dropdown'] = dropdown_list
        if dropdown_id==None:
            raise Exception('dropdown_id must be defined, if dropdown_list is defined.')
        item['dropdown_id'] = f'id-sidebar-dropdown-{dropdown_id}'
    item['active'] = 'active' if active else ''
    return item

def defaultContext(active_item=None):
    context = dict()
    context['title'] = 'My Dashboard'

    # Sidebar
    id_counter = 0
    id_counter_dropdown = 0
    sidebar = dict()
    sidebar['title'] = 'Menu'
    nav_items = list()
    nav_items.append(sidebarItem(
            text='Home', 
            icon='bi-house', 
            href=reverse('home')
    ))
    nav_items.append(sidebarItem(
            text='About', 
            icon='bi-info-circle', 
            href='#'
    ))

    dropdown_items = list()
    for movie in Movie.objects.all():
        dropdown_items.append(sidebarItem(
            text=movie.title, 
            href=reverse('movie', args=[movie.id])
        ))
        if active_item!=None and active_item==movie.title:
            dropdown_items[-1]['active'] = 'active'
    dropdown_items = sorted(dropdown_items, key=lambda x: x['text'])
    nav_items.append(sidebarItem(
        text='Movies',
        icon='bi-film',
        dropdown_list=dropdown_items,
        dropdown_id=id_counter_dropdown,
    ))
    if active_item!=None and active_item=='Movies':
        nav_items[-1]['active'] = 'active'
    id_counter_dropdown += 1
    sidebar['nav_items'] = nav_items
    context['sidebar'] = sidebar

    return context

class HomeView(TemplateView):
    template_name = 'my_dashboard/dashboard.html'

    def get_context_tv_shows(self):
        context = dict()
        tv_shows = list()
        schedule = get_tv_schedule(ep_date=date.today())
        if schedule!=None:
            for episode in schedule:
                tv_shows.append(
                    {
                        'show_name': episode.tv_show.title,
                        'episode_name': episode.title,
                        'episode_number': f'S{episode.season:02d}E{episode.episode:02d}',
                        'favorite': episode.tv_show.favorite,
                    }
                )
        print("DEBUG",tv_shows)
        context['tv_shows'] = tv_shows
        return context
    
    def get_context_movies(self):
        context = dict()
        movies = dict()
        parse_movie_feed()
        cutoff_date = date.today() - timedelta(days=AppSettings.get_key('movies_time_delta'))
        movie_insta_query = MovieInstance.objects.filter(date_added__gte=cutoff_date)
        for movie_instance in movie_insta_query:
            if movie_instance.movie.title not in movies:
                movies[movie_instance.movie.title] = {
                    'name': movie_instance.movie.title,
                    'year': movie_instance.movie.release_year,
                    'href': reverse('movie', args=[movie_instance.movie.id]), 
                    'resolutions': set(),
                    'groups': set()
                }
            movies[movie_instance.movie.title]['resolutions'].add(movie_instance.resolution)
            movies[movie_instance.movie.title]['groups'].add(movie_instance.group)
        context['movies'] = list()
        for movie in movies.values():
            movie['resolutions'] = ', '.join(sorted(movie['resolutions']))
            movie['groups'] = ', '.join(sorted(movie['groups']))
            context['movies'].append(movie)
        return context


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(defaultContext())
        context.update(self.get_context_tv_shows())
        context.update(self.get_context_movies())
        print("DEBUG",context)
        return context

class MovieView(DetailView):
    model = Movie
    template_name = 'my_dashboard/model_movies.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(defaultContext(active_item=self.object.title))
        context['page_heading'] = self.object.title
        context['movie_instances'] = [{
            'resolution': inst.resolution,
            'group': inst.group,
            'url': inst.url,
            'date_added': inst.date_added.strftime('%Y-%m-%d')
            }
            for inst in MovieInstance.objects.filter(movie=self.object)]
        return context