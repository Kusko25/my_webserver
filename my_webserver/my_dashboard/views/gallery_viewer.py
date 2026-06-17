from django.views.generic import FormView
from rest_framework.views import APIView
from rest_framework.response import Response
from functools import lru_cache
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from typing import Any, Optional
import requests
import json

from django.urls import reverse
from .views import SidebarMixin
from ..forms import GalleryViewerUrlForm
from ..variables import FRONTEND_TITLE_TEMPLATE

FRONTEND_GALLERY_TITLE_TEMPLATE = FRONTEND_TITLE_TEMPLATE % "Gallery - %s"

class GalleryView(SidebarMixin, FormView):
    template_name = 'my_dashboard/gallery_viewer/gallery_viewer.html'
    form_class = GalleryViewerUrlForm
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests: instantiate a blank version of the form."""
        if request.GET.get('url'):
            assert self.form_class is not None
            form = self.form_class(
                data={'url': request.GET['url']}
            )
            if form.is_valid():
                return self.form_valid(form)
        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        gallery = kwargs.pop('gallery', {'active': False})
        context = super().get_context_data(**kwargs)
        gallery['api_url'] = reverse('gallery-parse')
        context['gallery'] = gallery
        if "title" in gallery:
            context['title'] = FRONTEND_GALLERY_TITLE_TEMPLATE % gallery['title']
            gallery['page_title'] = FRONTEND_GALLERY_TITLE_TEMPLATE % gallery['title']
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
        assert gallery
        if "title" in gallery:
            gallery['page_title'] = FRONTEND_GALLERY_TITLE_TEMPLATE % gallery['title']
        response = Response(gallery)
        return response
    
    @classmethod
    def parse_url(cls, url, index=0) -> Optional[dict[str,Any]]:
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
        gallery: dict[str,Any] = {'active': True}
        gallery['url'] = url
        
        # Image URL
        comic = soup.find('div', id='spliced-comic')
        if comic is None:
            return None
        img_urls = []
        for img in comic.find_all('img'):
            img_url = str(img['src'])
            # Strip query string from URL
            components = urlparse(img_url)
            img_url = f'{components.scheme}://{components.netloc}{components.path}'
            img_urls.append(img_url)
        gallery['img_url'] = img_urls[index]
        
        # Misc
        assert soup.title is not None
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
    def parse_e_hentai_org(cls, url, get_next=True):
        """Parse the URL of an E-Hentai gallery."""
        parsed_url = urlparse(url)
        if '/g/' in parsed_url.path:
            soup = cls.get_soup(url)
            gallery_div = soup.find('div', id='gdt')
            assert gallery_div is not None
            first_link = gallery_div.find('a')
            assert first_link is not None
            return cls.parse_e_hentai_org(first_link['href'])
        
        soup = cls.get_soup(url)
        assert soup
        gallery: dict[str,Any] = {'active': True}
        gallery['url'] = url
        
        # Image URL
        gallery['img_url'] = soup.find('img', id='img')
        assert gallery['img_url']
        gallery['img_url'] = gallery['img_url']['src']
        
        # Misc
        assert soup.title is not None
        gallery['title'] = soup.title.string
        length = soup.select_one("div#i2 div.sn div")
        assert length
        length = length.text
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
        
        if gallery.get('next_url') and get_next:
            gallery['next_img_url'] = cls.parse_e_hentai_org(gallery['next_url'], get_next=False)['img_url']
        return gallery
    
    @staticmethod
    @lru_cache(maxsize=128)
    def get_soup(url, session=None):
        """Get the soup object for the given URL."""
        session = session or requests.Session()
        response = session.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')