from django.views.generic import FormView
from rest_framework.views import APIView
from rest_framework.response import Response
from functools import lru_cache
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
import json

from django.urls import reverse
from .views import SidebarMixin
from ..forms import GalleryViewerUrlForm

class GalleryView(SidebarMixin, FormView):
    template_name = 'my_dashboard/gallery_viewer/gallery_viewer.html'
    form_class = GalleryViewerUrlForm

    def get_context_data(self, **kwargs):
        gallery = kwargs.pop('gallery', {'active': False})
        context = super().get_context_data(**kwargs)
        gallery['api_url'] = reverse('gallery-parse')
        context['gallery'] = gallery
        context['js_data'] = json.dumps({'gallery': context['gallery']})
        return context
    
    def form_valid(self, form):
        context = self.get_context_data(gallery=GalleryViewerAPI.parse_url(form.cleaned_data['url']))
        return self.render_to_response(context)

class GalleryViewerAPI(APIView):
    def post(self, request):
        """Contains a url to be parsed. Response contains JSON with parsed data."""
        url = request.data.get('url')
        index = request.data.get('index',0)
        gallery = GalleryViewerAPI.parse_url(url, index)
        response = Response(gallery)
        print(url,index,response, response.data)
        return response
    
    @classmethod
    def parse_url(cls, url, index=0):
        """Parse the URL and return a dictionary with the parsed data."""
        parsed_url = urlparse(url)
        
        match parsed_url.netloc:
            case 'nortverse.com':
                return cls.parse_nortverse_com(url, index)
            case 'e-hentai.org':
                return cls.parse_e_hentai_org(url)
            case _:
                return {'active': False}
    
    @classmethod
    def parse_nortverse_com(cls, url, index=0):
        """Parse the URL of a Nortverse gallery."""
        soup:'BeautifulSoup' = cls.get_soup(url)
        gallery = {'active': True}
        gallery['url'] = url
        
        # Image URL
        comic = soup.find('div', id='spliced-comic')
        img_urls = []
        for img in comic.find_all('img'):
            img_url = img['src']
            # Strip query string from URL
            components = urlparse(img_url)
            img_url = f'{components.scheme}://{components.netloc}{components.path}'
            img_urls.append(img_url)
        gallery['img_url'] = img_urls[index]
        
        # Misc
        gallery['title'] = soup.title.string
        gallery['length'] = len(img_urls)
        
        # Next URL
        if index < len(img_urls) - 1:
            gallery['next_url'] = url
        else:
            gallery['next_url'] = soup.find('a', class_='next-comic')
            if gallery['next_url']:
                gallery['next_url'] = gallery['next_url']['href']
        
        # Previous URL
        if index > 0:
            gallery['prev_url'] = url
        else:
            gallery['prev_url'] = soup.find('a', class_='previous-comic')
            if gallery['prev_url']:
                gallery['prev_url'] = gallery['prev_url']['href']
        return gallery
    
    @classmethod
    def parse_e_hentai_org(cls, url):
        """Parse the URL of an E-Hentai gallery."""
        parsed_url = urlparse(url)
        if '/g/' in parsed_url.path:
            soup = cls.get_soup(url)
            gallery_div = soup.find('div', id='gdt')
            first_link = gallery_div.find('a')
            return cls.parse_e_hentai_org(first_link['href'])
        
        soup = cls.get_soup(url)
        gallery = {'active': True}
        gallery['url'] = url
        
        # Image URL
        gallery['img_url'] = soup.find('img', id='img')['src']
        
        # Misc
        gallery['title'] = soup.title.string
        length = soup.find('div', id='i2').find('div', class_='sn').find('div').text
        gallery['current'], gallery['length'] = (int(x.strip()) for x in length.split('/'))
        
        # Next URL
        gallery['next_url'] = soup.find('a', id='next')
        if gallery['next_url']:
            gallery['next_url'] = gallery['next_url']['href']
        if gallery['next_url'] == url:
            gallery['next_url'] = None
        
        # Previous URL
        gallery['prev_url'] = soup.find('a', id='prev')
        if gallery['prev_url']:
            gallery['prev_url'] = gallery['prev_url']['href']
        if gallery['prev_url'] == url:
            gallery['prev_url'] = None
        return gallery
    
    @staticmethod
    @lru_cache(maxsize=128)
    def get_soup(url, session=None):
        """Get the soup object for the given URL."""
        session = session or requests.Session()
        response = session.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')