import '../scss/styles.scss'
import "bootstrap-icons/font/bootstrap-icons.css";
import 'flatpickr/dist/flatpickr.min.css';
import '../css/custom_styles.css';
import 'font-awesome/css/font-awesome.min.css';
// import React from 'react';
// import { createRoot } from 'react-dom/client';
import flatpickr from "flatpickr";
import $ from 'jquery';
// import collapse from 'bootstrap/js/dist/collapse';
import { Collapse } from 'bootstrap';

// Async function that refreshes the page once an hour
async function refreshPage() {
    location.reload();
}
async function updateRSS() {
    if (send_api_get('update_rss','')) {
        console.log('RSS feeds updated');
    }
}

if (window.location.pathname === '/dashboard/') {
    // setInterval(refreshPage, 3600000);
    setInterval(updateRSS, 3600000);
    updateRSS();
}

async function update_topbar_gadget(switch_value, element) {
    switch (switch_value) {
        case 'headset':
            let data = await fetch_api_data_get('gadget_data','?gadget=headset');
            // If data is not false
            if (data) {
                // Update name field
                // Get element child with class 'device-name'
                element.querySelector('.device-name').textContent = data.name;
                // Status field
                element.querySelector('.device-status').textContent = data.text;
                // Icon field
                let icon = element.querySelector('.device-icon');
                // Remove all classes starting with 'bi-'
                icon.classList.remove(...Array.from(icon.classList).filter(c => c.startsWith('bi-')));
                // Add new class
                icon.classList.add('bi-' + data.icon);
            }
            break;
            // More cases can be added here
        default:
            console.error('Invalid value for switch_value');
    }
}

async function send_api_get(endpoint, params) {
    const url='api/' + endpoint + params;
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
    
        const json = await response.json();
        if (json.message) {
            console.log(json.message);
        }
        return true
      } catch (error) {
        console.error(error.message);
        return false
      }
}

async function fetch_api_data_get(endpoint, params) {
    const url='api/' + endpoint + params;
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
    
        const json = await response.json();
        return json
      } catch (error) {
        console.error(error.message);
        return false
      }
}

async function fetch_api_html_get(endpoint, params) {
    const url='api/html/' + endpoint + params;
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
    
        const html = await response.text();
        return html
    } catch (error) {
        console.error(error.message);
        return ''
    }
}

function refresh_component_html(component_id, html) {
    $(component_id).html(html);
    register_listeners();
}

function register_listeners() {
    $('.collapse').on('show.bs.collapse', function (e) {
        $(e.target).prev('.card-header').find('.bi-chevron-down').addClass('rotate-90');
    });

    $('.collapse').on('hide.bs.collapse', function (e) {
        $(e.target).prev('.card-header').find('.bi-chevron-down').removeClass('rotate-90');
    });
    $('#monitor-switch-2').on('click', function() {
        if (send_api_get('monitor_control','?monitor=2')) {
            console.log(this)
            if (this.classList.contains('bi-tv-fill')) {
                this.classList.replace('bi-tv-fill', 'bi-tv');
            }
            else {
                this.classList.replace('bi-tv', 'bi-tv-fill');
            }
        }
    });
    if ($('#navElHeadset').length) {
        // Add click event listener to the element with id 'navElHeadset'
        $('#navElHeadset').on('click', function() {
            // Call the function to update the gadget
            update_topbar_gadget('headset', $(this)[0]);
        });
        // Turn mouse pointer into hand when hovering over the element
        $('#navElHeadset').css('cursor', 'pointer');
    }
    $('#tvshow-container-refresh').css('cursor', 'pointer');
    $('#tvshow-container-refresh').on('click', async function() {
        let new_html = '';
        // Add fa-spin class to the element        
        $(this).addClass('fa-spin');
        new_html = await fetch_api_html_get('component/tv-shows/', '')
        if (new_html != '') {
            refresh_component_html('#tvshow-container', new_html);
        }
        console.log('TV Show container clicked');
    });
    $('#schedules-container-refresh').css('cursor', 'pointer');
    $('#schedules-container-refresh').on('click', async function() {
        let new_html = '';
        $(this).addClass('fa-spin');
        new_html = await fetch_api_html_get('component/schedules/', '')
        if (new_html != '') {
            refresh_component_html('#schedules-container', new_html);
        }
        console.log('Schedule container clicked');
    });
}

$(function() {
    // iterate over each element with the class 'datetimepicker'
    $('.datetimepicker').each(function() {
        // create a new flatpickr instance with the options
        flatpickr(this, {
            enableTime: true,
            dateFormat: "d-m-Y H:i",
            noCalendar: true,
            allowInput: true,
            minuteIncrement: 1,
            time_24hr: true,
            defaultDate: new Date(),
        });
    });
});

document.addEventListener('DOMContentLoaded', (event) => {
    register_listeners();
});