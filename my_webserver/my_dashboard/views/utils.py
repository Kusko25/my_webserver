from django.urls import reverse
from logging import getLogger
from typing import Optional
from ..models import AppSettings

from ..utils import call_external_tool, monitor_toggle
from PyP100 import PyP110
from scapy.layers.l2 import ARP, Ether
from scapy.sendrecv import srp
from ..variables import FRONTEND_TITLE_DEFAULT

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
    context['title'] = FRONTEND_TITLE_DEFAULT
    return context

def get_headset_data():
        context = dict()
        try:        
            ## Headset Battery
            headset_info = call_external_tool('headsetcontrol.exe', ['-o', 'json'], parseAsJson=True)
            assert isinstance(headset_info, dict)
            if len(headset_info.get('devices', [])) > 1:
                logger.warning('More than one headset detected, defaulting to first one')
            for device in headset_info.get('devices', []):
                # headset.name, headset.icon, headset.text
                context = {
                    'name': device.get('device', 'Unknown')
                }
                battery_status = device['battery']['status']
                battery_level = device['battery']['level']
                match battery_status:
                    case 'BATTERY_CHARGING':
                        context['icon'] = 'battery-charging'
                        context['text'] = 'Charging...' # During charging, level is always 100
                    case 'BATTERY_AVAILABLE':
                        if battery_level>85:
                            context['icon'] = 'battery-full'
                        elif battery_level>35:
                            context['icon'] = 'battery-half'
                        else:
                            context['icon'] = 'battery'
                        context['text'] = f'{battery_level}%'
                    case 'BATTERY_UNAVAILABLE':
                        context['icon'] = 'ban'
                        context['text'] = 'Unknown'
                    case _:
                        logger.warning(f'Unknown battery status: {battery_status}')
                        context['icon'] = 'ban'
                        context['text'] = 'Unknown'
                break
        except Exception as e:
            logger.error(f'Error while getting headset battery: {e}')
            return None
        return context

def get_p110_data():
    def get_ip(mac_address) -> Optional[str]:
        ip = "192.168.0.0/24"
        arp_request = ARP(pdst=ip)
        # Ethernet frame to broadcast the ARP
        broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
        # Combine the two
        arp_request_broadcast = broadcast / arp_request
        # Send request and receive response
        answered_list = srp(arp_request_broadcast, timeout=1, verbose=False)[0]
        for element in answered_list:
            if element[1].hwsrc == mac_address:
                return element[1].psrc
        return None
    
    context = dict()
    try:
        ## PC Power Consumption
        p110_ip = get_ip(AppSettings.get_key("p110_address"))
        if p110_ip is None:
            logger.warning("P110 not found on network")
            return None
        p110 = PyP110.P110(
            address=p110_ip,
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