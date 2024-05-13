from django.urls import reverse

from ..models import Movie


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
            text='Admin', 
            icon='bi-archive', 
            href=reverse('admin:index')
    ))
    nav_items.append(sidebarItem(
            text='Home', 
            icon='bi-house', 
            href=reverse('home')
    ))
    nav_items.append(sidebarItem(
            text='Register Medication Event', 
            icon='bi-plus',
            href=reverse('event-register-medication')
    ))
    nav_items.append(sidebarItem(
        text='Movies',
        icon='bi-film'
    ))
    if active_item!=None and active_item=='Movies':
        nav_items[-1]['active'] = 'active'
    id_counter_dropdown += 1
    sidebar['nav_items'] = nav_items
    context['sidebar'] = sidebar

    return context
