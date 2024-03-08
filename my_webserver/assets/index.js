// import React from 'react';
// import { createRoot } from 'react-dom/client';
import 'bootstrap/dist/css/bootstrap.min.css';
import "bootstrap-icons/font/bootstrap-icons.css";
// import 'bootstrap';
// flatpickr css
import 'flatpickr/dist/flatpickr.min.css';
import flatpickr from "flatpickr";
import $ from 'jquery';

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