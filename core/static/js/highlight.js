(function($) {

    var padding = 5;

    var offset = 0; /* Think the 'a' tag around the thumbnail has a border
		       that shifts the thumbnail down and to the right a couple pixels... so
		       we do the same with the highlights */

    function add_highlights(image) {
        if (image.data('highlighted')==true) {
            return
        }
        var width = image.width();
        var height = image.height();    
        if (width>0 && height>0) {
            image.data('highlighted', true)
            var script_name = image.data('script_name');
            var id = image.data('id');
            var words = image.data('words');
            $.getJSON(script_name+id+'coordinates/', function(all_coordinates) {
                image.wrap('<div class="highlight_words" style="display: inline-block; position: relative; margin: 0px; padding: 0px;" />');
                var div = image.parents("div.highlight_words")
		div.wrap('<div style="text-align: center" />')

                var vScale = height / all_coordinates["height"];
                var hScale = width / all_coordinates["width"];
                $.each(words.split(" "), function(index, word) {
                    var boxes = [];
                    var coordinates = all_coordinates["coords"][word];
                    for (k in coordinates) {
                        var v = coordinates[k];
                        div.append("<div style='position: absolute; " +
    "TOP: " +  (v[1] * vScale - padding/2.0 + offset) + 'px; ' +
    "LEFT: " +       (v[0] * hScale - padding/2.0 + offset) + 'px; ' +
    "HEIGHT: " +     (v[3] * vScale + padding) + 'px; ' +
    "WIDTH: " +      (v[2] * hScale + padding) + "px;'/>");

                    }
                });
            });
        }
    }

    function init() {
        $("img.highlight_words").load(function(i) {
            add_highlights($(this));
        });
        $("img.highlight_words").each(function(i) {
            if (this.complete) {
		add_highlights($(this));
	    }
	});
    };

    $(init);

})(jQuery)
