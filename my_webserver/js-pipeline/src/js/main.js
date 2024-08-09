import '../scss/styles.scss'
import "bootstrap-icons/font/bootstrap-icons.css";
import 'flatpickr/dist/flatpickr.min.css';
import '../css/custom_styles.css';
// import React from 'react';
// import { createRoot } from 'react-dom/client';
import flatpickr from "flatpickr";
import $ from 'jquery';
// import collapse from 'bootstrap/js/dist/collapse';
import { Collapse } from 'bootstrap';

// Async function that refreshes the page once an hour
async function refreshPage() {
    // await new Promise(resolve => setTimeout(resolve, 500));
    await new Promise(resolve => setTimeout(resolve, 3600000));
    location.reload();
}

if (window.location.pathname === '/dashboard/') {
    refreshPage();
}

async function send_api_get(endpoint, params) {
    const url='api/' + endpoint + params;
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
    
        const json = await response.json();
        console.log(json);
        return true
      } catch (error) {
        console.error(error.message);
        return false
      }
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
});