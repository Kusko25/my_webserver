import '../scss/styles.scss'
import "bootstrap-icons/font/bootstrap-icons.css";
import 'flatpickr/dist/flatpickr.min.css';
import '../css/custom_styles.css';

import $ from 'jquery';
import CanvasJS from '@canvasjs/charts';

window.onload = function () {
    
    var dps = []; // dataPoints
    var chart = new CanvasJS.Chart("chartContainer", {
        title :{
            text: "Power Consumption (W)"
        },
        data: [{
            type: "line",
            dataPoints: dps
        }]
    });
    
    var updateInterval = 3000;
    var dataLength = 20; // number of dataPoints visible at any point
    var api_url = '/dashboard/api/power_reading/';
    
    var updateChart = function (count) {
        let data = null;
        $.ajax({
            url: api_url,
            type: 'GET',
            async: false,
            success: function(response) {
                data = response;
            }
        });
        let xVal = data.timestamp;
        xVal = new Date(xVal);
        let yVal = data.power;
        yVal = Math.round(yVal/1000);
        dps.push({
            x: xVal,
            y: yVal
        });
    
        if (dps.length > dataLength) {
            dps.shift();
        }
    
        chart.render();
    };
    
    updateChart(dataLength);
    setInterval(function(){updateChart()}, updateInterval);
    
    }