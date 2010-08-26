function init_search_titles_form() {
    setup_states();
}

function setup_states() {
    select = $("select#state");
    select.append('<option value="">All</option>');
    $.getJSON('/states.json', function(states){
        for (state in states) {
            select.append('<option>' + states[state] + '</option>')
        }
    });
    select.change(load_counties);
    select.change(load_all_cities);
}

function load_counties() {
    // clear out pre-existing counties and cities
    county_select = $('select#county');
    county_select.empty().append('<option value="">All</option>');
    $('select#city').empty().append('<option value="">All</option>');

    // load up the counties for the selected state
    state = $('select#state').find('option:selected').text();
    $.getJSON('/counties/' + normalize(state) + '.json', function(counties){
        for (county in counties) {
            county_select.append('<option>' + counties[county] + '</option>');
        }
        county_select.change(load_cities);
    });
}

function load_all_cities() {
    state = $('select#state').find('option:selected').text();
    select = $('select#city');
    select.empty().append('<option value="">All</option>');
    $.getJSON('/cities/' + normalize(state) + '.json', function(cities){
        for (city in cities) {
            select.append('<option>' + cities[city] + '</option>');
        }
    });
}

function load_cities() {
    state = $('select#state').find('option:selected').text();
    county = $('select#county').find('option:selected').text();
    select = $('select#city');
    select.empty().append('<option value="">All</option>');
    // load 'All' counties is selected then load all cities
    if (county == 'All') {
        url = '/cities/' + normalize(state) + '.json';
    } 
    else {
        url = '/cities/' + normalize(state) + '/' + normalize(county) + '.json';
    }
    $.getJSON(url, function(cities) {
        select = $('select#city');
        for (city in cities) {
            select.append('<option>' + cities[city] + '</option>');
        }
    });
}

// needed to convert human readable state names to a format recognized
// by the django url router: "New York" -> "new_york"

function normalize(s) {
    s = s.toLowerCase();
    parts = s.split(' ');
    return parts.join('_');
}
