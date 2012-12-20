(function($) {

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
                image.wrap('<div class="highlight_words" style="display: inline-block; position: relative; margin: 0px; padding: 0px; height: auto; width: auto;" />');
                var div = image.parents("div.highlight_words")
		div.wrap('<div style="text-align: center" />')

                var vScale = 100 / all_coordinates["height"];
                var hScale = 100 / all_coordinates["width"];
                $.each(words.split(" "), function(index, word) {
                    var boxes = [];
                    var coordinates = all_coordinates["coords"][word];
                    for (k in coordinates) {
                        var v = coordinates[k];
                        div.append("<div style='position: absolute; " +
    "TOP: " +  (v[1] * vScale) + '%; ' +
    "LEFT: " +       (v[0] * hScale) + '%; ' +
    "HEIGHT: " +     (v[3] * vScale) + '%; ' +
    "WIDTH: " +      (v[2] * hScale) + "%;'/>");

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
