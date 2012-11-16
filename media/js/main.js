function normalize(s) {
    s = s.toLowerCase();
    var parts = s.split(' ');
    return parts.join('_');
}

jQuery(function($){
    function getUrlVars(){
        var vars = [], hash;
        var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
        for(var i = 0; i < hashes.length; i++){
            hash = hashes[i].split('=');
            vars.push(hash[0]);
            vars[hash[0]] = hash[1];
        }
        return vars;
    }

    $("#tabs-container").on('chronam.tabsloaded', function () {
    $("#box-tabs").tabs({collapsible: true});
    $("#box-tabs").show();
    if ($("#tabs-container").hasClass("collapsed")) {
        $("#box-tabs").tabs('select', '#tab_search');
    };

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
    var start_year = $('#id_date1').val();
    var end_year = $('#id_date2').val();

    $('#id_datefrom').datepicker({defaultDate: new Date(start_year, 1-1, 1), showOn: "focus", yearRange: start_year+":"+end_year, currentText: '', changeMonth: true, changeYear: true, closeText: 'Done'});
    $('#id_dateto').datepicker({defaultDate: new Date(end_year, 12-1, 31), showOn: "focus", yearRange: start_year+":"+end_year, currentText: '', changeMonth: true, changeYear: true});

    // bind form field .click's
    $('#id_datefrom, #id_dateto').click( function() {
        $('#id_radiorange').attr('checked', 'checked');});
    $('#id_radioyear').click( function() {
        $('#id_dateto, #id_datefrom').val('');});
    $('#id_radiorange').click( function() {
        $('#id_datefrom').val('01/01/'+start_year); 
        $('#id_dateto').val('12/31/'+end_year);
    });

    $("input#id_sequence").val(1);
    if (getUrlVars()["sequence"]==1){
        $("input#id_sequence").attr('checked', 'checked');
        $("input#id_char_sequence").val('');
    } else {
        $("input#id_sequence").attr('checked', false);
    }

    if (getUrlVars()["dateFilterType"]=="range"){ 
        $('#id_radiorange').attr('checked', 'checked');
        $("select#id_date2 option[value='"+end_year+"']").attr("selected", true);
    } else if (getUrlVars()["dateFilterType"]=="yearRange"){
        $('#id_radioyear').attr('checked', 'checked');
        $('#id_dateto, #id_datefrom').val('');
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
            $("input#id_datefrom, input#id_dateto").attr('disabled', 'disabled');
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
