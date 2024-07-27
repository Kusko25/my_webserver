from django.urls import reverse
from logging import getLogger
from ..models import AppSettings

from ..utils import call_external_tool

logger = getLogger(__name__)


def sidebarItem(text='', icon=None, href=None, dropdown_list=None, dropdown_id=None, active=False):
    item = dict()
    item['text'] = text
    if icon is not None:
        item['icon'] = icon
    if href is not None:
        item['href'] = href
    if dropdown_list is not None:
        item['dropdown'] = dropdown_list
        if dropdown_id is None:
            raise Exception('dropdown_id must be defined, if dropdown_list is defined.')
        item['dropdown_id'] = f'id-sidebar-dropdown-{dropdown_id}'
    item['active'] = 'active' if active else ''
    return item

def defaultContext(active_item=None):
    context = dict()
    context['title'] = 'My Dashboard'

    # Sidebar
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
        text='Power Monitor',
        icon='bi-speedometer2',
        href=reverse('power-monitor')
    ))
    if active_item is not None and active_item=='Movies':
        nav_items[-1]['active'] = 'active'
    id_counter_dropdown += 1
    sidebar['nav_items'] = nav_items
    context['sidebar'] = sidebar

    return context

def get_context_topbar():
        context = dict()
        try:        
            ## Headset Battery
            headset_info = call_external_tool('headsetcontrol.exe', ['-o', 'json'], parseAsJson=True)
            if len(headset_info.get('devices', [])) > 1:
                logger.warning('More than one headset detected, defaulting to first one')
            for device in headset_info.get('devices', []):
                # headset.name, headset.icon, headset.text
                context['headset'] = {
                    'name': device.get('device', 'Unknown')
                }
                battery_status = device['battery']['status']
                battery_level = device['battery']['level']
                if battery_status == 'BATTERY_CHARGING':
                    context['headset']['icon'] = 'battery-charging'
                    context['headset']['text'] = 'Charging...' # During charging, level is always 100
                elif battery_status == 'BATTERY_AVAILABLE':
                    if battery_level>85:
                        context['headset']['icon'] = 'battery-full'
                    elif battery_level>35:
                        context['headset']['icon'] = 'battery-half'
                    else:
                        context['headset']['icon'] = 'battery'
                    context['headset']['text'] = f'{battery_level}%'
                else:
                    logger.warning(f'Unknown battery status: {battery_status}')
                    context['headset']['icon'] = 'ban'
                    context['headset']['text'] = 'Unknown'
                break
        except Exception as e:
            logger.error(f'Error while getting headset battery: {e}')
        
        try:
            ## PC Power Consumption
            from PyP100 import PyP110
            p110 = PyP110.P110(
                address=AppSettings.get_key('p110_address'),
                email=AppSettings.get_key('p110_email'),
                password=AppSettings.get_key('p110_password')
            )
            energy_data = p110.getEnergyUsage()
            context['pc_power'] = {
                "today": "Unknown",
                "current": "Unknown"
            }
            if 'today_energy' in energy_data:
                context['pc_power']['today'] = f"{energy_data['today_energy']/1000:.2f} kWh"
            if 'current_power' in energy_data:
                context['pc_power']['current'] = f"{energy_data['current_power']/1000:.2f} W"
        except Exception as e:
            logger.error(f'Error while getting PC power consumption: {e}')
        return {'topbar': context}