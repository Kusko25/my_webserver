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
});