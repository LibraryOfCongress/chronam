function getUrlVars(){
    var searchString = window.location.search.substring(1);
    var vars = {};
    if (searchString) {
       var hash,
       hashes = searchString.split('&');
       for(var i=0; i<hashes.length; i++){
           hash = hashes[i].split('=');
           vars[unescape(hash[0])] = unescape(hash[1]);
       }
    }
    return vars;
}

jQuery(function($){
    var vars = getUrlVars();
    $("#tabs-container").on('chronam.tabsloaded', function () {
    $("#box-tabs").tabs({collapsible: true});
    $("#box-tabs").show();
    var selectedTab = 0;
    $("#box-tabs li a").each(function(index) {
        if ($.bbq.getState("tab") == $(this).attr("href").replace("#", "")) {
            selectedTab = index;
        };
    });
    $("#box-tabs").tabs({'select': function(event, ui){$.bbq.pushState({"tab": $(ui.tab).attr("href").replace("#", "")})},
                         'selected': selectedTab})

    // simple search tab
    // bind form field click
    var proxtext = $("#id_proxtext");
    var default_search_text = 'enter one or more search words'
    if(proxtext.val() == ''){
        proxtext.val(default_search_text).css('color','#bbbbbb');
        proxtext.focus( function() {
            $(this).val('').css('color','#000000');
            $(this).unbind('focus');
        });
    };

    // removes default search text to prevent it from submitting
    $("form#fulltext").submit(function(event){
        if (proxtext.val() == default_search_text){
            proxtext.attr('value','');
        };
        $(this).unbind('submit').submit();
    });

    // init datepickers
    var start_year = $("#id_date1").val();
    var end_year = $("#id_date2").val();

    // disable issue_date selector on page load
    $("#id_date_month").prop("disabled", "disabled");
    $('#id_date_day').prop("disabled", "disabled");

    // enable issue_date selector when checkbox is on
    $("#id_issue_date").change(function() {
        if ($('#id_issue_date').is(':checked')) {
            $("#id_date_month").prop("disabled", false);
            $('#id_date_day').prop("disabled", false);
        } 
        else 
        {
            $("#id_date_month").prop("disabled", "disabled");
            $('#id_date_day').prop("disabled", "disabled");
        }
    });

    // disable options in 'from' year dropdown based on option selected in 'to' dropdown
    $("select#id_date1").change(function(){
        // enable all options first before selectively disabling some
        $('select option').each(function() {        
            $(this).attr('disabled', false);
        });
        var _start_yr = parseInt($(this).val());
        $("select#id_date2 > option").each(function() {
            if(parseInt(this.text) < _start_yr)
            {
                $(this).attr('disabled', true);
            }
        });
    });


    $('#id_date_from').datepicker({defaultDate: new Date(start_year, 1-1, 1), showOn: "focus", yearRange: start_year+":"+end_year, currentText: '', changeMonth: true, changeYear: true, closeText: 'Done'});
    $('#id_date_to').datepicker({defaultDate: new Date(end_year, 12-1, 31), showOn: "focus", yearRange: start_year+":"+end_year, currentText: '', changeMonth: true, changeYear: true});

    // bind form field .click's
    $('#id_date_from, #id_date_to').click( function() {
        $('#id_radiorange').attr('checked', 'checked');});
    $('#id_radioyear').click( function() {
        $('#id_date_to, #id_date_from').val('');});
    $('#id_radiorange').click( function() {
        $('#id_date_from').val('01/01/'+start_year); 
        $('#id_date_to').val('12/31/'+end_year);
    });

    $("input#id_sequence").val(1);
    if (vars["sequence"]==1){
        $("input#id_sequence").attr('checked', 'checked');
        $("input#id_char_sequence").val('');
    } else {
        $("input#id_sequence").attr('checked', false);
    }

    if (vars["dateFilterType"]=="range"){ 
        $('#id_radiorange').attr('checked', 'checked');
        $("select#id_date2 option[value='"+end_year+"']").attr("selected", true);
    } else if (vars["dateFilterType"]=="yearRange"){
        $('#id_radioyear').attr('checked', 'checked');
        $('#id_date_to, #id_date_from').val('');
    } else {
        $('#id_radioyear').attr('checked', 'checked');
        $("select#id_date2 option[value='"+end_year+"']").attr("selected", true);
    }

    // hide adv search tab
    $("#id_close_tab_advanced_search").click(function(event) {
        event.preventDefault();
        $("a[href='#tab_advanced_search']").click();
    });        

    $("#id_close_tab_newspapers").click(function(event) {
        event.preventDefault();
        $("a[href='#tab_newspapers']").click();
    });        

    // removes unselected elements to prevent from submitting
    $("form#fulltext2").submit(function(event){
        event.preventDefault();
        if ($("#fulltext2 input[type=radio]:checked").attr('id')=='id_radioyear'){
            $("input#id_date_from, input#id_date_to").attr('disabled', 'disabled');
        }else{
            $("select#id_date1, select#id_date2").attr('disabled', 'disabled');};
        if (isNaN(parseInt($("input#id_char_sequence").val()))){
            $("input#id_char_sequence").val("");}
        if ($("#id_char_sequence").val() == ""){
            $("input#id_char_sequence").attr('disabled', 'disabled');
        }else{
            $("input#id_sequence").attr('checked', false);
            $("input#id_sequence").attr('disabled', 'disabled');
        }
        $(this).unbind('submit').submit();
    });

    $("#adv_reset").click(function(event){
        event.preventDefault();
        $(':text, select', '#fulltext2').val('');
        $(':input', '#fulltext2')
        .removeAttr('checked')
        .removeAttr('selected');
        $('#id_radioyear').attr('checked', 'checked');
        $("select#id_date2 option[value='"+end_year+"']").attr("selected", true);
    });
    });
}); 
