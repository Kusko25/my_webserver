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
import { Collapse, Modal } from 'bootstrap';
import { createApp } from "vue";
import WeatherGadget from '../vue/weather.vue'

createApp(WeatherGadget).mount('#weather-gadget')

class APIFunctions {
    static async send_api_get(endpoint, params) {
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
    
    static async fetch_api_data_get(endpoint, params) {
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
    
    static async fetch_api_html_get(endpoint, params) {
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
}

class UtilityFunctions {
    static refresh_component_html(component_id, html) {
        $(component_id).html(html);
    }
}

class NotifcationFunctions {
    static requestNotificationPermission() {
        if (Notification.permission !== 'granted') {
            Notification.requestPermission().then(function (permission) {
                if (permission === 'granted') {
                    console.log('Notification permission granted.');
                }
                else {
                    console.log('Notification permission denied.');
                }
                NotifcationFunctions.updateNotificationSwitch();
            });
        }
    }
    // Send a notification
    static sendNotification(message, icon='') {
        if (Notification.permission === 'granted') {
            var notification = new Notification('Notification', {
                body: message,
                icon: icon,
            });
        }
    }
    static notificationsEnabled() {
        return Notification.permission === 'granted';
    }

    static registerListeners() {
        $('#notifications-switch').on('click', function() {
            if (!NotifcationFunctions.notificationsEnabled()) {
                Notification.requestPermission().then(function (permission) {
                    if (permission === 'granted') {
                        console.log('Notification permission granted.');
                    }
                    else {
                        console.log('Notification permission denied.');
                    }
                    NotifcationFunctions.updateNotificationSwitch();
                });
            }
        });
    }

    static updateNotificationSwitch() {
        if (NotifcationFunctions.notificationsEnabled()) {
            $('#notifications-switch').removeClass('bi-megaphone').addClass('bi-megaphone-fill');
        }
        else {
            $('#notifications-switch').removeClass('bi-megaphone-fill').addClass('bi-megaphone');
        }
    }

    static async checkNotifications() {
        // Not API for now. Just a scheduled notification at a specific time
        let now = new Date();
        // At 17:00
        if (now.getHours() === 17 && now.getMinutes() === 0) {
            let suffix = Math.random() > 0.1 ? 'please.' : 'now bitch!';
            NotifcationFunctions.sendNotification('Go lift the barbell, ' + suffix);
        }
    }

    static run() {
        console.log('Setting up notifications.')
        NotifcationFunctions.updateNotificationSwitch();
        NotifcationFunctions.registerListeners();
        // Timer once a minute to check for new notifications and display them
        setInterval(NotifcationFunctions.checkNotifications, 60000);
    }
}

class CalorieGadget {
    static async refresh() {
        let new_html = '';
            new_html = await APIFunctions.fetch_api_html_get('component/calories/', '')
            if (new_html != '') {
                UtilityFunctions.refresh_component_html('#navElCal', new_html);
                CalorieGadget.registerListeners();
            }
            console.log('Refreshed Calorie Gadget.');
    }
    static registerListeners() {
        $('#navElCal-refresh').on('click', CalorieGadget.refresh)
        $('#navElCal-add50').on('click', async function() {
            let new_html = '';
            new_html = await APIFunctions.fetch_api_html_get('component/calories/', '?calories=50')
            if (new_html != '') {
                UtilityFunctions.refresh_component_html('#navElCal', new_html);
                CalorieGadget.registerListeners();
            }
            console.log('Calories: +50');
        });
        $('#navElCal-add100').on('click', async function() {
            let new_html = '';
            new_html = await APIFunctions.fetch_api_html_get('component/calories/', '?calories=100')
            if (new_html != '') {
                UtilityFunctions.refresh_component_html('#navElCal', new_html);
                CalorieGadget.registerListeners();
            }
            console.log('Calories: +100');
        });
    }
}

class FormHandler {
    static async submitForm(form_id) {
        let form_modal = document.getElementById(form_id);
        let form = form_modal.querySelector('form');
        let formData = new FormData(form);
        let url = form.getAttribute('action');
        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
            });
            if (response.status === 200) {
                console.log('Form submitted successfully');
            }
            else if (response.status === 400) {
                console.error('Form submission failed. Bad request.');
            }
            else {
                console.error('Form submission failed. Unknown error.');
            }
            return response;
        } catch (error) {
            console.error(error.message);
            return null;
        }
    }
    static async fetchForm(form_id) {
        let url = 'api/form/' + form_id;
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`Response status: ${response.status}`);
            }
            else {
                // Return the html form
                return response.text();
            }
        }
        catch (error) {
            console.error(error.message);
            return ''
        }
    }

    static updateForm(form_id, data) {
        let form = document.getElementById(form_id);
        // Get modal body
        let modal_body = form.querySelector('.modal-body');
        // Remove all children
        while (modal_body.firstChild) {
            modal_body.removeChild(modal_body.firstChild);
        }
        // Add form to modal body
        modal_body.innerHTML = data;
    }

    static registerListener(form_id) {
        let form_modal = document.getElementById(form_id);
        let form = form_modal.querySelector('form');
        let submit_button = form.querySelector('button[type="submit"]');
        submit_button.addEventListener('click', async function(event) {
            event.preventDefault();
            let response = await FormHandler.submitForm(form_id);
            if (response.status === 200) {
                // Refresh the page
                location.reload();
            }
            else if (response.status === 400) {
                // Display the returned form with errors
                let data = await response.text();
                FormHandler.updateForm(form_id, data);
            }
        });
    }
}

async function updateRSS() {
    if (APIFunctions.send_api_get('update_rss','')) {
        console.log('RSS feeds updated');
    }
}

async function update_topbar_gadget(switch_value, element) {
    switch (switch_value) {
        case 'headset':
            let data = await APIFunctions.fetch_api_data_get('gadget_data','?gadget=headset');
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


function register_listeners() {
    $('.collapse').on('show.bs.collapse', function (e) {
        $(e.target).prev('.card-header').find('.bi-chevron-down').addClass('rotate-90');
    });

    $('.collapse').on('hide.bs.collapse', function (e) {
        $(e.target).prev('.card-header').find('.bi-chevron-down').removeClass('rotate-90');
    });
    $('#monitor-switch-2').on('click', function() {
        if (APIFunctions.send_api_get('monitor_control','?monitor=2')) {
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
        new_html = await APIFunctions.fetch_api_html_get('component/tv-shows/', '')
        if (new_html != '') {
            UtilityFunctions.refresh_component_html('#tvshow-container', new_html);
            register_listeners();
        }
        console.log('TV Show container clicked');
    });
    $('#schedules-container-refresh').css('cursor', 'pointer');
    $('#schedules-container-refresh').on('click', async function() {
        let new_html = '';
        $(this).addClass('fa-spin');
        new_html = await APIFunctions.fetch_api_html_get('component/schedules/', '')
        if (new_html != '') {
            UtilityFunctions.refresh_component_html('#schedules-container', new_html);
            register_listeners();
        }
        console.log('Schedule container clicked');
    });
    CalorieGadget.registerListeners();
}

document.addEventListener('DOMContentLoaded', (event) => {
    register_listeners();
    if (window.location.pathname === '/dashboard/') {
        // setInterval(refreshPage, 3600000);
        setInterval(updateRSS, 3600000);
        updateRSS();
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
    NotifcationFunctions.run();
    try {
        // var modal_ids should be defined in the template and available in the global scope
        modal_ids.forEach(FormHandler.registerListener);
    }
    catch (error) {
        console.error("Error registering form listeners.");
        console.error(error);
    }
});