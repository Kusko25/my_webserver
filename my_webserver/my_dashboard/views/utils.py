from django.urls import reverse
from logging import getLogger
from ..models import AppSettings

from ..utils import call_external_tool, monitor_toggle

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
    return context

def get_headset_data():
        context = dict()
        try:        
            ## Headset Battery
            headset_info = call_external_tool('headsetcontrol.exe', ['-o', 'json'], parseAsJson=True)
            if len(headset_info.get('devices', [])) > 1:
                logger.warning('More than one headset detected, defaulting to first one')
            for device in headset_info.get('devices', []):
                # headset.name, headset.icon, headset.text
                context = {
                    'name': device.get('device', 'Unknown')
                }
                battery_status = device['battery']['status']
                battery_level = device['battery']['level']
                if battery_status == 'BATTERY_CHARGING':
                    context['icon'] = 'battery-charging'
                    context['text'] = 'Charging...' # During charging, level is always 100
                elif battery_status == 'BATTERY_AVAILABLE':
                    if battery_level>85:
                        context['icon'] = 'battery-full'
                    elif battery_level>35:
                        context['icon'] = 'battery-half'
                    else:
                        context['icon'] = 'battery'
                    context['text'] = f'{battery_level}%'
                else:
                    logger.warning(f'Unknown battery status: {battery_status}')
                    context['icon'] = 'ban'
                    context['text'] = 'Unknown'
                break
        except Exception as e:
            logger.error(f'Error while getting headset battery: {e}')
            return None
        return context

def get_p110_data():
    context = dict()
    try:
        ## PC Power Consumption
        from PyP100 import PyP110
        p110 = PyP110.P110(
            address=AppSettings.get_key('p110_address'),
            email=AppSettings.get_key('p110_email'),
            password=AppSettings.get_key('p110_password')
        )
        energy_data = p110.getEnergyUsage()
        context = {
            "today": "Unknown",
            "current": "Unknown"
        }
        if 'today_energy' in energy_data:
            context['today'] = f"{energy_data['today_energy']/1000:.2f} kWh"
        if 'current_power' in energy_data:
            context['current'] = f"{energy_data['current_power']/1000:.2f} W"
    except Exception as e:
        logger.error(f'Error while getting PC power consumption: {e}')
        return None
    return context

def get_context_topbar():
    context = dict()
    context['headset'] = get_headset_data()
    if not context['headset']:
        del context['headset']
    context['pc_power'] = get_p110_data()
    if not context['pc_power']:
        del context['pc_power']
        
    return {'topbar': context}