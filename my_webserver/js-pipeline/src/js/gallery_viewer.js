import $ from 'jquery';
import '../css/gallery_styles.css';

const api_url = js_data['gallery']['api_url'];
var active = js_data['gallery']['active'];
if (active) {
    var img_url = js_data['gallery']['img_url'];
    // next_img_url if present
    if ('next_img_url' in js_data['gallery']) {
        var next_img_url = js_data['gallery']['next_img_url'];
    }
    else {
        var next_img_url = null;
    }
    var length = js_data['gallery']['length'];
    var index = 0;
    var next_url = js_data['gallery']['next_url'];
    var prev_url = js_data['gallery']['prev_url'];
    var title = js_data['gallery']['title'];
    var src = js_data['gallery']['url'];
    var loading = false;
    var current = null;
}

// Function to get the CSRF token from the cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

async function api_call(data_url, data_index) {
    let response = await fetch(api_url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken, // Include the CSRF token in the headers
        },
        body: JSON.stringify({
            'url': data_url,
            'index': data_index,
        }),
    });
    let resp_data = await response.json();
    img_url = resp_data['img_url'];
    if ('next_img_url' in resp_data) {
        next_img_url = resp_data['next_img_url'];
    }
    length = resp_data['length'];
    next_url = resp_data['next_url'];
    prev_url = resp_data['prev_url'];
    title = resp_data['title'];
    src = resp_data['url'];
    if ('current' in resp_data) {
        current = resp_data['current'];
    }
    else {
        current = null;
    }
    if ('page_title' in resp_data) {
        document.title = resp_data['page_title'];
    }
    // console.log('API call successful');
}

async function handle_next_click() {
    // console.log('Next clicked');
    if (next_url === null) {
        return;
    }
    if (index === length-1) {
        index = 0;
    }
    else {
        index++;
    }
    loading = true;
    update_html();
    await api_call(next_url, index);
    loading = false;
    update_html();
}

async function handle_prev_click() {
    // console.log('Prev clicked');
    if (prev_url === null) {
        return;
    }
    if (index === 0) {
        index = 0;
    }
    else {
        index--;
    }
    loading = true;
    update_html();
    await api_call(prev_url, index);
    loading = false;
    update_html();
}

function handle_img_click() {
    // console.log('Image clicked');
    // Iter through classes img-fluid, img-scaled, img-full
    let img = $('#gallery_img');
    if (img.hasClass('img-fluid')) {
        img.removeClass('img-fluid');
        img.addClass('img-scaled');
    }
    else if (img.hasClass('img-scaled')) {
        img.removeClass('img-scaled');
        img.addClass('img-full');
    }
    else {
        img.removeClass('img-full');
        img.addClass('img-fluid');
    }
}

function update_html() {
    // console.log('Updating HTML');
    // console.log('img_url:', img_url);
    // console.log('length:', length);
    // console.log('index:', index);
    // console.log('next_url:', next_url);
    // console.log('prev_url:', prev_url);
    // console.log('title:', title);
    // console.log('src:', src);

    
    $('#gallery_img').attr('src', img_url);
    $('#gallery_img').attr('alt', img_url);
    $('#gallery_next_img').attr('src', next_img_url); // For preloading the next image
    $
    if (loading) {
        $('#gallery_img').addClass('img-loading');
        $('#gallery_load_indicator').removeClass('spinner-disabled');
        $('#gallery_load_indicator').addClass('spinner-overlay');
    }
    else {
        $('#gallery_img').removeClass('img-loading');
        $('#gallery_load_indicator').removeClass('spinner-overlay');
        $('#gallery_load_indicator').addClass('spinner-disabled');
    }

    if (current !== null) {
        $('#gallery_index').text(current);
    }
    else {
        $('#gallery_index').text(index+1);
    }
    $('#gallery_count').text(length);
    $('#gallery_title').text(title);
    $('#gallery_src').attr('href', img_url);
    $('#gallery_src').text(src);

    if (prev_url === null) {
        $('#gallery_prev').addClass('disabled');
    }
    else {
        $('#gallery_prev').removeClass('disabled');
    }
    if (next_url === null) {
        $('#gallery_next').addClass('disabled');
    }
    else {
        $('#gallery_next').removeClass('disabled');
    }
}

$(function() {
    if (!active) {
        // console.log('Gallery is not active');
        return;
    }
    // console.log('Gallery is active, setting up event listeners');
    $('#gallery_next').on('click', handle_next_click);
    $('#gallery_prev').on('click', handle_prev_click);
    // Register left and right arrow key press events
    $(document).on('keydown', function(e) {
        if (e.key === 'ArrowLeft') {
            handle_prev_click();
        }
        else if (e.key === 'ArrowRight') {
            handle_next_click();
        }
    });

    $('#gallery_img').on('click', handle_img_click);
    update_html();
});