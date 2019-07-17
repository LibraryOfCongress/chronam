/* globals OpenSeadragon, jQuery, ChronAmSearch */

(function($) {
    var page_url;
    var tile_url;
    var iiif_url;
    var coordinates_url;
    var navigation_url;
    var width;
    var height;
    var static_url;
    var printButtonConfigured = false;

    function checkPrintButtonHander() {
        // We're effectively racing the LOCShare code which is loaded asynchronously
        // using a convoluted system which does not fire an event when it's completed
        // and waits until after all page resources have been loaded before triggering. We'll

        if (!printButtonConfigured) {
            var $pb = $(".locshare-print-button a");

            if ($pb.length > 0) {
                $(".locshare-print-button a").attr(
                    "href",
                    $("#clip").attr("href")
                );

                $pb.off("click").on("click", function(event) {
                    event.stopImmediatePropagation();
                    window.open(this.href, "print");
                    return false;
                });

                printButtonConfigured = true;
            }
        }
    }

    function resizePrint(event) {
        var viewer = event.eventSource;
        var image = viewer.source;
        var zoom = viewer.viewport.getZoom();
        var size = new OpenSeadragon.Rect(
            0,
            0,
            image.dimensions.x,
            image.dimensions.y
        );
        var container = viewer.viewport.getContainerSize();
        var fit_source = fitWithinBoundingBox(size, container);
        var total_zoom = fit_source.x / image.dimensions.x;
        var container_zoom = fit_source.x / container.x;
        var level = (zoom * total_zoom) / container_zoom;
        var box = getDisplayRegion(
            viewer,
            new OpenSeadragon.Point(
                parseInt(image.dimensions.x * level),
                parseInt(image.dimensions.y * level)
            )
        );
        var scaledBox = new OpenSeadragon.Rect(
            parseInt(box.x / level),
            parseInt(box.y / level),
            parseInt(box.width / level),
            parseInt(box.height / level)
        );
        var d = fitWithinBoundingBox(box, new OpenSeadragon.Point(681, 817));
        var dimension =
            page_url +
            "print/image_" +
            d.x +
            "x" +
            d.y +
            "_from_" +
            scaledBox.x +
            "," +
            scaledBox.y +
            "_to_" +
            scaledBox.getBottomRight().x +
            "," +
            scaledBox.getBottomRight().y;
        $("#clip").attr("href", dimension);
        $(".locshare-print-button a").attr("href", dimension);
        checkPrintButtonHander();
    }

    function fitWithinBoundingBox(d, max) {
        if (d.width / d.height > max.x / max.y) {
            return new OpenSeadragon.Point(
                max.x,
                parseInt((d.height * max.x) / d.width)
            );
        } else {
            return new OpenSeadragon.Point(
                parseInt((d.width * max.y) / d.height),
                max.y
            );
        }
    }

    function getDisplayRegion(viewer, source) {
        //Determine portion of scaled image that is being displayed
        var box = new OpenSeadragon.Rect(0, 0, source.x, source.y);
        var container = viewer.viewport.getContainerSize();
        var bounds = viewer.viewport.getBounds();
        //If image is offset to the left
        if (bounds.x > 0) {
            box.x =
                box.x -
                viewer.viewport.pixelFromPoint(new OpenSeadragon.Point(0, 0)).x;
        }
        //If full image doesn't fit
        if (box.x + source.x > container.x) {
            box.width =
                container.x -
                viewer.viewport.pixelFromPoint(new OpenSeadragon.Point(0, 0)).x;
            if (box.width > container.x) {
                box.width = container.x;
            }
        }
        //If image is offset up
        if (bounds.y > 0) {
            box.y =
                box.y -
                viewer.viewport.pixelFromPoint(new OpenSeadragon.Point(0, 0)).y;
        }
        //If full image doesn't fit
        if (box.y + source.y > container.y) {
            box.height =
                container.y -
                viewer.viewport.pixelFromPoint(new OpenSeadragon.Point(0, 0)).y;
            if (box.height > container.y) {
                box.height = container.y;
            }
        }
        return box;
    }

    function addOverlay(viewer, x1, y1, x2, y2) {
        var div = document.createElement("div");
        var rect = new OpenSeadragon.Rect(x1, y1, x2, y2);

        div.className = "overlay";
        viewer.drawer.addOverlay(div, rect);
    }

    function addOverlays(event) {
        var viewer = event.eventSource;
        var params = $.deparam.fragment();
        var words = params["words"] || "";

        $.getJSON(coordinates_url, function(all_coordinates) {
            var scale = 1 / all_coordinates["width"];

            var matchingWords = ChronAmSearch.matchWords(
                words,
                all_coordinates
            );

            $.each(matchingWords, function(index, word_on_page) {
                $.each(all_coordinates["coords"][word_on_page], function(
                    index,
                    value
                ) {
                    addOverlay(
                        viewer,
                        value[0] * scale,
                        value[1] * scale,
                        value[2] * scale,
                        value[3] * scale
                    );
                });
            });
        });
    }

    function getTileUrl(level, column, row) {
        var px = 0;
        if (column != 0) {
            px = this.tileSize * column - this.tileOverlap;
        }
        var py = 0;
        if (row != 0) {
            py = this.tileSize * row - this.tileOverlap;
        }
        var scale = this.getLevelScale(level);
        var dimensionsScaled = this.dimensions.times(scale);

        // find the dimension of the tile, adjust for no
        // overlap data on top and left edges
        var sx = this.tileSize + (column == 0 ? 1 : 2) * this.tileOverlap;
        var sy = this.tileSize + (row == 0 ? 1 : 2) * this.tileOverlap;

        // adjust size for single-tile levels where the image
        // size is smaller than the regular tile size, and for
        // tiles on the bottom and right edges that would
        // exceed the image bounds.
        sx = Math.min(sx, dimensionsScaled.x - px);
        sy = Math.min(sy, dimensionsScaled.y - py);

        var x1 = parseInt(px / scale);
        var y1 = parseInt(py / scale);
        var x2 = parseInt((px + sx) / scale);
        var y2 = parseInt((py + sy) / scale);

        // tile width/height dimension can't be more than image sides
        var tile_width = Math.min(parseInt(sx), x2 - x1);
        var tile_height = Math.min(parseInt(sy), y2 - y1);

        if (iiif_url) {
            return (
                iiif_url +
                x1 +
                "," +
                y1 +
                "," +
                (x2 - x1) +
                "," +
                (y2 - y1) +
                "/" +
                tile_width +
                "," +
                tile_height +
                "/0/default.jpg"
            );
        } else {
            return (
                tile_url +
                "image_" +
                tile_width +
                "x" +
                tile_height +
                "_from_" +
                x1 +
                "," +
                y1 +
                "_to_" +
                x2 +
                "," +
                y2 +
                ".jpg"
            );
        }
    }

    function updateSearchNav(data) {
        if (!data) return;

        var jQuerynav_result = $(".nav_result");
        jQuerynav_result.find("a.backtoresults").attr("href", data.results);
        jQuerynav_result.find(".current").text(data.current);
        jQuerynav_result.find(".total").text(data.total);

        if (data.next_result) {
            jQuerynav_result
                .find(".next")
                .removeClass("disabled")
                .find("a")
                .wrapInner($("<a>").attr("href", data.next_result));
        }
        if (data.previous_result) {
            jQuerynav_result
                .find(".previous")
                .removeClass("disabled")
                .find("a")
                .wrapInner($("<a>").attr("href", data.previous_result));
        }
        jQuerynav_result.slideDown("fast");
    }

    function addSearchNav() {
        var params, search_qs;

        params = $.extend($.deparam.querystring(), $.deparam.fragment());
        search_qs = $.param(params, true);

        if (!search_qs || !search_qs.match(/searchType/)) return;

        $.ajax({
            url: navigation_url + search_qs,
            dataType: "json",
            cache: true,
            success: updateSearchNav
        });
    }

    function initPage() {
        addSearchNav();

        page_url = $("#page_data").data("page_url");
        tile_url = $("#page_data").data("tile_url");
        iiif_url = $("#page_data").data("iiif-url");
        coordinates_url = $("#page_data").data("coordinates_url");
        navigation_url = $("#page_data").data("navigation_url");
        width = $("#page_data").data("width");
        height = $("#page_data").data("height");
        static_url = $("#page_data").data("static_url");

        if (!width || !height) {
            return;
        }

        var ts;

        if (iiif_url) {
            ts = [iiif_url];
        } else {
            var tileSize = 512;
            var tileOverlap = 1;
            var minLevel = 8;
            var maxLevel = Math.ceil(
                Math.log(Math.max(width, height)) / Math.log(2)
            );

            ts = new OpenSeadragon.TileSource(
                width,
                height,
                tileSize,
                tileOverlap,
                minLevel,
                maxLevel
            );
            ts.getTileUrl = getTileUrl;
        }

        var viewer = new OpenSeadragon.Viewer({
            id: "viewer_container",
            toolbar: "item-ctrl",
            prefixUrl: static_url,
            autoHideControls: false,
            nextButton: "next",
            previousButton: "previous",
            tileSources: ts,
            timeout: 60000,
            showNavigator: true
        });

        viewer.addHandler("open", addOverlays);
        viewer.addHandler("open", resizePrint);
        viewer.addHandler("animation-finish", resizePrint);
    }

    $(initPage);
})(jQuery);
