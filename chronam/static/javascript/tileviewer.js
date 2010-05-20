function ImageViewer(imageViewerElement, tileSize, 
                     fullImageWidth, fullImageHeight, 
                     pagePath, url) {
    this.imageViewerElement = imageViewerElement;
    initializeImageViewer(this.imageViewerElement, tileSize,
                          fullImageWidth, fullImageHeight, pagePath, url, []);
}

ImageViewer.HIGHLITE_IMAGE = "/images/red_60.png"; 

ImageViewer.prototype.zoomIn = function() {
    zoomImageUp(this.imageViewerElement, undefined);
}
ImageViewer.prototype.zoomOut = function() {
    zoomImageDown(this.imageViewerElement, undefined);
}
ImageViewer.prototype.reset = function() {
    resetViewer(this.imageViewerElement);
}
ImageViewer.prototype.startRegion = function() {
    startRegion(this.imageViewerElement);
}
ImageViewer.prototype.printRegion = function() {
    return printRegion(this.imageViewerElement);
}

//------------------------------------------------------------

/*
Inspired and borrowed from http://mike.teczno.com/giant/pan/gsv.js

Optimizations for JP2 decoding on the server:
* Retrieves the fewest number of tiles (only what is needed on the screen).
* Retrieves with the fewest number of requests (combines requests for adjacent tiles into a request for a single image).
* Makes all requests on tile borders.
* Uses power of 2 zooming (so no resizing required).
Optimizations for the browser:
* Retrieves with the fewest number of requests (see http://www.die.net/musings/page_load_time/ for why this is good).

*/

var MAX_LEVEL = 6;
var HAVE = 0;
var NEED = 1;
var NOTHING = 2;
var MODE_ZOOM = 0;
var MODE_REGION = 1;

function getEvent(event)
{
    if(event == undefined) {
        return window.event;
    }
    
    return event;
}

//Called to initialize the ImageViewer
function initializeImageViewer(imageViewer, tileSize, fullImageWidth, fullImageHeight, pagePath, url, highliteBoxes)
{
    for(var child = imageViewer.firstChild; child; child = child.nextSibling) {
        if(child.className == 'surface') {
            imageViewer.activeSurface = child;
            child.imageViewer = imageViewer;
        
        } else if(child.className == 'tilewell') {
            imageViewer.tileWell = child;
            child.imageViewer = imageViewer;
        
        } else if(child.className == 'highlitewell') {
            imageViewer.highliteWell = child;
            child.imageViewer = imageViewer;        
        } else if(child.className == 'regionhighlite') {
            imageViewer.regionHighlite = child;        
        }
    }    

    imageViewer.pagePath = pagePath
    imageViewer.url = url;
    imageViewer.tileSize = tileSize;    

    imageViewer.defaultDimensions = new Dimensions(imageViewer.offsetWidth, imageViewer.offsetHeight);
    imageViewer.imageSet = new ImageSet(new Dimensions(fullImageWidth, fullImageHeight), tileSize);
    imageViewer.defaultLevel = 1;
    while(imageViewer.imageSet.getImage(imageViewer.defaultLevel).scaledDimensions.width < imageViewer.defaultDimensions.width && imageViewer.defaultLevel < MAX_LEVEL)
    {
        imageViewer.defaultLevel++;
    }
    imageViewer.defaultLevel--;    
 
    //Adjust size of ImageViewer    
    imageViewer.dimensions = new Dimensions(imageViewer.offsetWidth, imageViewer.defaultDimensions.height > imageViewer.imageSet.getImage(imageViewer.defaultLevel).scaledDimensions.height ? imageViewer.defaultDimensions.height : imageViewer.imageSet.getImage(imageViewer.defaultLevel).scaledDimensions.height);
    imageViewer.style.width = imageViewer.dimensions.width+'px';
    imageViewer.style.height = imageViewer.dimensions.height+'px';

    imageViewer.dimensions = new Dimensions(imageViewer.offsetWidth, imageViewer.imageSet.getImage(imageViewer.defaultLevel).scaledDimensions.height);
    imageViewer.style.width = imageViewer.dimensions.width+'px';
    imageViewer.style.height = imageViewer.dimensions.height+'px';
    imageViewer.imageTileOffset = new Point(0, 0);
    imageViewer.start = new Point(0, 0);
    imageViewer.lastMouse = new Point(0, 0);
    imageViewer.mode = MODE_ZOOM;
    
    imageViewer.tileViewerSet = new TileViewerSet();
    //This means that a page can only have a single imageviewer
    document.body.imageViewer = imageViewer;
    document.body.onmouseup = releaseViewer;

    imageViewer.highliteViewer = new HighliteViewer(highliteBoxes);
    appendHighliteBoxes(imageViewer, highliteBoxes);

    resetViewer(imageViewer);
}

function updateViewer(imageViewer) {
    cleanImageViewer(imageViewer);
    prepareImageViewer(imageViewer);
    positionImageViewer(imageViewer, new Point(0, 0));
}

function appendHighliteBoxes(imageViewer, boxes) {
    var highliteViewer = imageViewer.highliteViewer;
    //Place the imgs for highlites in highliteWell
    for(var i = 0; i < boxes.length; i++)
    {
        var hl = new Highlite(boxes[i]);
        highliteViewer.highlites.push(hl);
        imageViewer.highliteWell.appendChild(hl.img);
    }
}

//Cleans the ImageViewer.  Should be called before changing to a new level.
function cleanImageViewer(imageViewer)
{    
    //Remove existing imgs from tileWell
    while(imageViewer.tileWell.hasChildNodes())
    {
        imageViewer.tileWell.removeChild(imageViewer.tileWell.firstChild);
    }
    imageViewer.tileViewerSet.getViewer(imageViewer.level).clean();
    
    //No need to remove existing imgs from highlitewell, since will just be resizing and moving

}

//Prepares the ImageViewer for displaying a particular level.  Called after cleaning and level has been changed.
function prepareImageViewer(imageViewer)
{    
    //Create imgs for an existing ViewerTiles
    var viewer = imageViewer.tileViewerSet.getViewer(imageViewer.level);
    for(var i = 0; i < viewer.viewerTiles.length; i += 1)
    {
        viewer.viewerTiles[i].createImg();
        imageViewer.tileWell.appendChild(viewer.viewerTiles[i].img);            

    }

    //Resize highlites
    imageViewer.highliteViewer.resize(imageViewer.imageSet.getImage(imageViewer.level).scaleFactor);
    
}

//Updates the ImageViewer when the position has changed
function positionImageViewer(imageViewer, mouse)
{
    //Position image tiles
    var image = imageViewer.imageSet.getImage(imageViewer.level);
    image.positionImageTiles(imageViewer, mouse);
    //Create viewer tiles for needed image tiles
    var viewer = imageViewer.tileViewerSet.getViewer(imageViewer.level);
    for(var c = 0; c < image.columns; c += 1)
    {
        for(var r = 0; r < image.rows; r += 1)
        {
            var imageTile = image.imageTiles[c][r];
            if (imageTile.status == NEED)
            {
                var dimensions = new Dimensions(imageTile.scaledDimensions.width, imageTile.scaledDimensions.height);
                var box = new Box(imageTile.fullBox.x, imageTile.fullBox.y, imageTile.fullBox.width, imageTile.fullBox.height);
                //Check imageTiles below
                var r2 = r+1;
                var addedRowCount = 0;
                while(r2 < image.rows && image.imageTiles[c][r2].status == NEED)
                {                    
                    //console.log("Expanding by a row");
                    dimensions.height += image.imageTiles[c][r2].scaledDimensions.height;
                    box.height += image.imageTiles[c][r2].fullBox.height;
                    image.imageTiles[c][r2].status = HAVE;
                    addedRowCount += 1;
                    r2 += 1;
                }
                //Check imageTiles to right
                var c2 = c+1;
                while(c2 < image.columns && image.imageTiles[c2][r].status == NEED)
                {                    
                    //console.log("Expanding by a column");
                    dimensions.width += image.imageTiles[c2][r].scaledDimensions.width;
                    box.width += image.imageTiles[c2][r].fullBox.width;
                    image.imageTiles[c2][r].status = HAVE;
                    for(var i = 1; i <= addedRowCount; i += 1)
                    {
                        image.imageTiles[c2][r+i].status = HAVE;
                    }
                    c2 += 1;
                }

                //Create viewer tile                
                var viewerTile = new ViewerTile(imageTile.column, imageTile.row, dimensions, box, imageViewer.pagePath, imageViewer.url);
                viewerTile.createImg();
                viewer.viewerTiles.push(viewerTile);
                imageViewer.tileWell.appendChild(viewerTile.img);
                imageTile.status = HAVE;
            }
        }
    }
    //Position viewer tiles
    viewer.positionViewerTiles(imageViewer, mouse);

    //Position the highlites
    imageViewer.highliteViewer.position(imageViewer, mouse, image.scaleFactor);


}

function monitorMove(event)
{
    var ev = getEvent(event);
    var windowDimension = getWindowDimensions();
    
    if (ev.clientX <= 10 || ev.clientX >= windowDimension.x - 25 || ev.clientY <= 10 || ev.clientY >= windowDimension.y - 10) 
    {        
        releaseViewer(event);
    }
}

function getWindowDimensions() {
  var windowDimension = new Dimensions(0, 0);
  if( typeof( window.innerWidth ) == 'number' ) {
    //Non-IE
    windowDimension.x = window.innerWidth;
    windowDimension.y = window.innerHeight;
  } else if( document.documentElement && ( document.documentElement.clientWidth || document.documentElement.clientHeight ) ) {
    //IE 6+ in 'standards compliant mode'
    windowDimension.x = document.documentElement.clientWidth;
    windowDimension.y = document.documentElement.clientHeight;
  } else if( document.body && ( document.body.clientWidth || document.body.clientHeight ) ) {
    //IE 4 compatible
    windowDimension.x = document.body.clientWidth;
    windowDimension.y = document.body.clientHeight;
  }
  
  return windowDimension;
}

function moveViewer(event)
{
    var imageViewer = document.body.imageViewer;
    var ev = getEvent(event);
    //var mouse = localizeCoordinates(imageViewer, new Point(ev.clientX, ev.clientY));
    var mouse = getMouse(ev);
 
    if (mouse.x <= 0 || mouse.y <= 0 || mouse.x >= imageViewer.dimensions.width || mouse.y >= imageViewer.dimensions.height)
    {
        return;
    }
    if (imageViewer.mode == MODE_ZOOM)
    {
        positionImageViewer(imageViewer, mouse);
        imageViewer.lastMouse = mouse;
    }
    else
    {
        var widthDelta = mouse.x - imageViewer.start.x;
        if (widthDelta > 0)
        {
            imageViewer.regionHighlite.box.width = widthDelta;
        }
        else
        {
            imageViewer.regionHighlite.box.x = mouse.x;
            imageViewer.regionHighlite.box.width = widthDelta * -1;
        }
        var heightDelta = mouse.y - imageViewer.start.y;
        if (heightDelta > 0)
        {
            imageViewer.regionHighlite.box.height = heightDelta;
        }
        else
        {
            imageViewer.regionHighlite.box.y = mouse.y;
            imageViewer.regionHighlite.box.height = heightDelta * -1;
        }
        setRegionHighlite(imageViewer.regionHighlite);
    }
}

function fitWithinBoundingBox(d, max) {
    if (d.width/d.height > max.width/max.height) {
        return new Dimensions(max.width,
                              parseInt(d.height * max.width/d.width));
    } else {
        return new Dimensions(parseInt(d.width * max.height/d.height),
                              max.height);
    }
}

function printRegion(imageViewer)
{
    var unscaledBox = getDisplayRegion(imageViewer);
    var scaledBox = unscaledBox.getScaledBox(imageViewer.imageSet.getImage(imageViewer.level).scaleFactor);
    var d = fitWithinBoundingBox(unscaledBox, new Dimensions(681, 817))
    return imageViewer.pagePath + "print/image_" + d.width + "x" + d.height + "_from_" + parseInt(scaledBox.x) + "," + parseInt(scaledBox.y) + "_to_" + parseInt(scaledBox.getX2()) + "," + parseInt(scaledBox.getY2())
}

function getDisplayRegion(imageViewer)
{
    //Determine portion of scaled image that is being displayed
    var image = imageViewer.imageSet.getImage(imageViewer.level);
    var box = new Box(0, 0, image.scaledDimensions.width, image.scaledDimensions.height);
    //If image is offset to the left
    if (imageViewer.imageTileOffset.x < 0)
    {
        box.x = imageViewer.imageTileOffset.x * -1;
        box.width = image.scaledDimensions.width + imageViewer.imageTileOffset.x;
    }
    //If full image doesn't fit
    if (imageViewer.imageTileOffset.x + image.scaledDimensions.width > imageViewer.dimensions.width)
    {
        box.width = imageViewer.dimensions.width - imageViewer.imageTileOffset.x;
        if (box.width > imageViewer.dimensions.width)
        {
            box.width = imageViewer.dimensions.width;
        }
    }
    //If image is offset up
    if (imageViewer.imageTileOffset.y < 0)
    {
        box.y = imageViewer.imageTileOffset.y * -1;
        box.height = image.scaledDimensions.height + imageViewer.imageTileOffset.y;
    }
    //If full image doesn't fit
    if (imageViewer.imageTileOffset.y + image.scaledDimensions.height > imageViewer.dimensions.height)
    {
        box.height = imageViewer.dimensions.height - imageViewer.imageTileOffset.y;
        if (box.height > imageViewer.dimensions.height)
        {
            box.height = imageViewer.dimensions.height;
        }
    }
    return box;
}

//The box of the image within the ImageViewer window
function getImageBox(imageViewer)
{
    var image = imageViewer.imageSet.getImage(imageViewer.level);
    var box = new Box(0, 0, image.scaledDimensions.width, image.scaledDimensions.height);
    if (imageViewer.imageTileOffset.x > 0)
    {
        box.x = imageViewer.imageTileOffset.x;
    }
    else
    {
        box.width += imageViewer.imageTileOffset.x;
    }

    if (imageViewer.imageTileOffset.y > 0)
    {
        box.y = imageViewer.imageTileOffset.y;
    }
    else
    {
        box.height += imageViewer.imageTileOffset.y;
    }

    if (box.getX2() > imageViewer.dimensions.width)
    {
        box.width = imageViewer.dimensions.width;
        if (imageViewer.imageTileOffset.x > 0)
        {
            box.width -= imageViewer.imageTileOffset.x;
        }
    }
    if (box.getY2() > imageViewer.dimensions.height)
    {
        box.height = imageViewer.dimensions.height;
        if (imageViewer.imageTileOffset.y > 0)
        {
            box.height -= imageViewer.imageTileOffset.y;
        }
    }
    return box;
}

function getMouse(event)
{
    return new Point((event.offsetX != undefined) ? event.offsetX : event.layerX, (event.offsetY != undefined) ? event.offsetY : event.layerY);
}

function pressViewer(event)
{
    var imageViewer = this.imageViewer;
    var ev = getEvent(event);
    //var mouse = localizeCoordinates(imageViewer, ev);
    var mouse = getMouse(ev);

    if (! getImageBox(imageViewer).containsPoint(mouse))
    {
        return;
    }

    imageViewer.pressed = true;
    this.onmousemove = moveViewer;
    document.body.onmousemove = monitorMove;
    imageViewer.start = mouse;
    disableSelection(document.body);

    if (imageViewer.mode == MODE_ZOOM)
    {
        imageViewer.tileWell.style.cursor = imageViewer.activeSurface.style.cursor = 'move';        
    }
    else
    {
        imageViewer.regionHighlite.box = new Box(mouse.x, mouse.y, 0, 0);
        setRegionHighlite(imageViewer.regionHighlite);
    }
}

function disableSelection(target)
{
    if (typeof target.onselectstart!="undefined") //IE route
        target.onselectstart=function(){return false}
    else if (typeof target.style.MozUserSelect!="undefined") //Firefox route
	    target.style.MozUserSelect="none"
    else //All other route (ie: Opera)
	    target.onmousedown=function(){return false}
}

function enableSelection(target)
{
    if (typeof target.onselectstart!="undefined") //IE route
	    target.onselectstart=null
    else if (typeof target.style.MozUserSelect!="undefined") //Firefox route
	    target.style.MozUserSelect=null
    else //All other route (ie: Opera)
	    target.onmousedown=null
}

function setRegionHighlite(regionHighlite)
{
   regionHighlite.style.left = regionHighlite.box.x + "px";
   regionHighlite.style.top = regionHighlite.box.y + "px";
   regionHighlite.style.width = regionHighlite.box.width + "px";
   regionHighlite.style.height = regionHighlite.box.height + "px";
   if (regionHighlite.box.width == 0 && regionHighlite.box.height == 0)
   {
        regionHighlite.style.visibility = "hidden";        
   }
   else
   {
        regionHighlite.style.visibility = "visible";
   }
}  

function releaseViewer(event)
{
    var ev = getEvent(event);
    var imageViewer = document.body.imageViewer;
    //var mouse = localizeCoordinates(imageViewer, new Point(ev.clientX, ev.clientY));       
    var mouse = getMouse(ev);
    //IE doesn't support event.target
    var target = ev.srcElement ? ev.srcElement : ev.target;        
    if (target != imageViewer.activeSurface)
    {
        mouse = imageViewer.lastMouse;
    }

    if(imageViewer.pressed) {
        imageViewer.activeSurface.onmousemove = null;
        document.body.onmousemove = null;
        imageViewer.tileWell.style.cursor = imageViewer.activeSurface.style.cursor = 'default';
        imageViewer.pressed = false;
        enableSelection(document.body);
        if (imageViewer.mode == MODE_ZOOM)
        {
            imageViewer.imageTileOffset.x += (mouse.x - imageViewer.start.x);
            imageViewer.imageTileOffset.y += (mouse.y - imageViewer.start.y);
        }
        else
        {
            imageViewer.regionHighlite.box = new Box(0,0,0,0);
            setRegionHighlite(imageViewer.regionHighlite);
            imageViewer.mode = MODE_ZOOM;
            var scaledSelectionBox = new Box(imageViewer.start.x-imageViewer.imageTileOffset.x, imageViewer.start.y-imageViewer.imageTileOffset.y, mouse.x - imageViewer.start.x, mouse.y - imageViewer.start.y);
            zoomRegion(imageViewer, scaledSelectionBox);
            
        }

    }
}

function zoomRegion(imageViewer, scaledSelectionBox)
{
    //console.log("scaledSelectionBox corner is %d, %d, width is %d, and height is %d", scaledSelectionBox.x, scaledSelectionBox.y, scaledSelectionBox.width, scaledSelectionBox.height);
    //Determine fullSelectionBox
    var scaleFactor = imageViewer.imageSet.getImage(imageViewer.level).scaleFactor;
    var fullSelectionBox = new Box(scaledSelectionBox.x * scaleFactor, scaledSelectionBox.y * scaleFactor, scaledSelectionBox.width * scaleFactor, scaledSelectionBox.height * scaleFactor);
    //console.log("fullSelectionBox corner is %d, %d, width is %d, and height is %d", fullSelectionBox.x, fullSelectionBox.y, fullSelectionBox.width, fullSelectionBox.height);
    
    //Determine what is the highest level that can display the entire selection
    var canDisplay = false;
    var level = MAX_LEVEL;
    while (canDisplay == false)
    {
        scaleFactor = imageViewer.imageSet.getImage(level).scaleFactor;
        var dimensions = new Dimensions(Math.ceil(fullSelectionBox.width / scaleFactor), Math.ceil(fullSelectionBox.height / scaleFactor));
        if (dimensions.width < imageViewer.dimensions.width && dimensions.height < imageViewer.dimensions.width)
        {
            canDisplay = true;
        }
        else
        {
            level--;
        }
    }    
    //console.log("Level is %d", level);
    
    imageViewer.start.x = 0;
    imageViewer.start.y = 0;
    var center = scaledSelectionBox.getCenter();
    var image = imageViewer.imageSet.getImage(imageViewer.level);
    imageViewer.imageTileOffset.x = Math.round(imageViewer.dimensions.width / 2) - center.x;
    imageViewer.imageTileOffset.y = Math.round(imageViewer.dimensions.height / 2) - center.y;
    positionImageViewer(imageViewer, new Point(0,0));
    zoomImage(imageViewer, undefined, level - imageViewer.level);
}

function startRegion(imageViewer)
{
    imageViewer.tileWell.style.cursor = imageViewer.activeSurface.style.cursor = 'crosshair';
    imageViewer.mode = MODE_REGION;
}

function zoomImage(imageViewer, mouse, direction)
{
    var newLevel = imageViewer.level + direction;
    if (newLevel < 1 || newLevel > MAX_LEVEL)
    {
        return;
    }
    //Clean up before changing level
    cleanImageViewer(imageViewer);
    imageViewer.level = newLevel;
     //Prepare for displaying the new level
    prepareImageViewer(imageViewer);
    
    if(mouse == undefined) {
        var mouse = new Point(imageViewer.dimensions.width / 2, imageViewer.dimensions.height / 2);
    }
    
    // pixel position within the image is a function of the
    // upper-left-hand corner of the viewe in the page,
    // the click position (event), and the image position within
    // the viewer (dim).
    var oldPoint = new Point(imageViewer.imageTileOffset.x, imageViewer.imageTileOffset.y);
    imageViewer.imageTileOffset.x = mouse.x - ((mouse.x - oldPoint.x) * Math.pow(2, direction));
    imageViewer.imageTileOffset.y = mouse.y - ((mouse.y - oldPoint.y) * Math.pow(2, direction));
    imageViewer.start = mouse;
    positionImageViewer(imageViewer, mouse);
}

function zoomImageUp(imageViewer, mouse)
{
    zoomImage(imageViewer, mouse, 1);
}

function zoomImageDown(imageViewer, mouse)
{
    zoomImage(imageViewer, mouse, -1);
}

function resetViewer(imageViewer)
{
    imageViewer.regionHighlite.box = new Box(0,0,0,0);
    setRegionHighlite(imageViewer.regionHighlite);
    
    if (imageViewer.level != undefined)
    {
        cleanImageViewer(imageViewer);
    }
    imageViewer.level = imageViewer.defaultLevel;
    //console.log("Changing level to %d", imageViewer.level);
    prepareImageViewer(imageViewer);

    var image = imageViewer.imageSet.getImage(imageViewer.level);
    imageViewer.imageTileOffset.x = Math.round(((imageViewer.dimensions.width - image.scaledDimensions.width)/ 2));
    imageViewer.imageTileOffset.y = Math.round(((imageViewer.dimensions.height - image.scaledDimensions.height)/ 2));

    imageViewer.activeSurface.onmousedown = pressViewer;    
    imageViewer.start.x = 0;
    imageViewer.start.y = 0; // this is reset each time that the mouse is pressed anew
    imageViewer.pressed = false;

    positionImageViewer(imageViewer, new Point(0, 0));
}

//**************************************
// OBJECTS
//**************************************

//Point Object
function Point(x, y)
{
    this.x = x;
    this.y = y;
}

//Dimension Object
function Dimensions(width, height)
{
    this.width = width;
    this.height = height;
}

//Box Object
function Box(x, y, width, height)
{
    this.x = x;
    this.y = y;
    this.width = width;
    this.height = height;
    this.getX2 = boxGetX2;
    this.getY2 = boxGetY2;
    this.getCenter = boxGetCenter;
    this.getScaledBox = boxScale;
    this.containsPoint = boxContainsPoint;
        
}

function boxContainsPoint(point)
{
    if (point.x >= this.x && point.x <= this.getX2() && point.y >= this.y && point.y <= this.getY2())
    {
        return true;
    }
    return false;
}

function boxGetCenter()
{
    return new Point(Math.round(this.x + (this.width / 2)), Math.round(this.y + (this.height / 2)));
}

function boxGetX2()
{
    return this.x + this.width;;
}

function boxGetY2()
{
    return this.y + this.height;
}

function boxScale(scaleFactor)
{
    return new Box(this.x * scaleFactor, this.y * scaleFactor, this.width * scaleFactor, this.height * scaleFactor);
}

//Image Set Object
function ImageSet(fullDimensions, tileSize)
{
    this.fullDimensions = fullDimensions;
    this.tileSize = tileSize;
    this.images = [];
    this.getImage = getImage;
}

function getImage(level)
{
    if (this.images[level] == undefined)
    {
        this.images[level] = new ImageZ(this.fullDimensions, this.tileSize, level);
    }
    return this.images[level];
}

//Image Object
//Full is for full image
//Scaled is for scaled image
//Safari doesn't like this being called an Image, hence ImageZ
function ImageZ(fullDimensions, tileSize, level)
{
    this.level = level;
    this.scaleFactor = Math.pow(2, MAX_LEVEL - level);
    this.fullDimensions = fullDimensions;
    this.scaledDimensions = new Dimensions(Math.ceil(fullDimensions.width / this.scaleFactor), Math.ceil(fullDimensions.height / this.scaleFactor));
    this.scaledTileSize = tileSize;
    this.fullTileSize = tileSize * this.scaleFactor;
    this.columns = Math.ceil(this.fullDimensions.width / this.fullTileSize);
    this.rows = Math.ceil(this.fullDimensions.height / this.fullTileSize);
    this.imageTiles = [];
    for(var c = 0; c < this.columns; c +=1 )
    {
        var imageTileCol = [];
        for(var r = 0; r < this.rows; r+=1)
        {            
            var imageTileBox = new Box(c * this.fullTileSize, r * this.fullTileSize, this.fullTileSize, this.fullTileSize);
            if (imageTileBox.getX2() > this.fullDimensions.width)
            {
                imageTileBox.width = this.fullDimensions.width - imageTileBox.x;
            }
            if (imageTileBox.getY2() > this.fullDimensions.height)
            {
                imageTileBox.height = this.fullDimensions.height - imageTileBox.y;
            }
            var imageTile = new ImageTile(c, r, imageTileBox, this.scaleFactor);
            imageTileCol.push(imageTile);            
        }
        this.imageTiles.push(imageTileCol);
    }

    this.positionImageTiles = positionImageTiles;
}

function positionImageTiles(imageViewer, mouse)
{   
    //Figure out what we need
    for(var c = 0; c < this.columns; c+= 1)
    {
        for(var r = 0; r < this.rows; r+= 1)
        {
            var imageTile = this.imageTiles[c][r];            
            imageTile.viewerBox.x = ((c * imageViewer.tileSize) + imageViewer.imageTileOffset.x + (mouse.x - imageViewer.start.x));
            imageTile.viewerBox.width = imageTile.scaledDimensions.width;
            imageTile.viewerBox.y = ((r * imageViewer.tileSize) + imageViewer.imageTileOffset.y + (mouse.y - imageViewer.start.y))
            imageTile.viewerBox.height = imageTile.scaledDimensions.height;
            if (imageTile.status != HAVE)
            {
                //Determine if visible
                if (((imageTile.viewerBox.getX2() > 0 && imageTile.viewerBox.x < imageViewer.dimensions.width) || (imageTile.viewerBox.x < imageViewer.dimensions.width && imageTile.viewerBox.getX2() > 0)) && ((imageTile.viewerBox.getY2() > 0 && imageTile.viewerBox.y < imageViewer.dimensions.height) || (imageTile.viewerBox.y < imageViewer.dimensions.height && imageTile.viewerBox.getY2() > 0)))
                {
                    imageTile.status = NEED;
                }
            }
        }
    }

}



//Image Tile Object
function ImageTile(column, row, fullBox, scaleFactor)
{
    this.column = column;
    this.row = row;
    this.fullBox = fullBox;
    this.scaledDimensions = new Dimensions(Math.ceil(this.fullBox.width / scaleFactor), Math.ceil(this.fullBox.height / scaleFactor));
    this.viewerBox = new Box(0, 0, 0, 0);
    this.status = NOTHING;
}

//TileViewerSet object
function TileViewerSet()
{
    this.viewers = [];
    this.getViewer = getViewer;
}

function getViewer(level)
{
    if (this.viewers[level] == undefined)
    {
        this.viewers[level] = new TileViewer();
    }
    return this.viewers[level];
}

//TileViewer object
function TileViewer()
{
    this.viewerTiles = [];
    this.positionViewerTiles = positionViewerTiles;
    this.clean = cleanViewer;
}

function cleanViewer()
{
    for(var i=0; i < this.viewerTiles.length; i += 1)
    {
        this.viewerTiles[i].img = null;
    }

}

function positionViewerTiles(imageViewer, mouse)
{
    for(var i = 0; i < this.viewerTiles.length; i += 1)
    {
        var viewerTile = this.viewerTiles[i];
        viewerTile.box.x = Math.floor(((viewerTile.column * imageViewer.tileSize) + imageViewer.imageTileOffset.x + (mouse.x - imageViewer.start.x)));
        viewerTile.img.style.left = viewerTile.box.x + 'px';
        viewerTile.box.y = Math.floor(((viewerTile.row * imageViewer.tileSize) + imageViewer.imageTileOffset.y + (mouse.y - imageViewer.start.y)));
        viewerTile.img.style.top = viewerTile.box.y + 'px';

    }
}

function ViewerTile(column, row, dimensions, fullBox, pagePath, url)
{
    //console.info("Creating new ViewerTile (%d, %d) with a width of %d and height of %d", column, row, dimensions.width, dimensions.height);
    this.column = column;
    this.row = row;
    this.img = null;
    this.box = new Box(0, 0, dimensions.width, dimensions.height);

    this.source = pagePath + "image_" + this.box.width + "x" + this.box.height + "_from_" + fullBox.x + "," + fullBox.y + "_to_" + fullBox.getX2() + "," + fullBox.getY2() + ".jpg";

    //console.info("Source is " + this.source);
    this.createImg = createImg;
}

function createImg()
{
    this.img = document.createElement('img');
    this.img.className = 'tile';
    this.img.style.width = this.box.width+'px';
    this.img.style.height = this.box.height+'px';
    this.img.src = this.source;
}

//HighliteViewer object
function HighliteViewer(highliteBoxes)
{
    this.highlites = [];
    for(var i=0; i < highliteBoxes.length; i++)
    {
        if (highliteBoxes[i] != null)
        {
            this.highlites.push(new Highlite(highliteBoxes[i]));
        }
    }
    this.resize = resizeHighlites;
    this.position = positionHighlites;
}

function resizeHighlites(scaleFactor)
{
    for(var i=0; i < this.highlites.length; i++)
    {
        this.highlites[i].resize(scaleFactor);
    }
}

function positionHighlites(imageViewer, mouse, scaleFactor)
{
    for(var i=0; i < this.highlites.length; i++)
    {
        this.highlites[i].position(imageViewer, mouse, scaleFactor);
    }
}


//Highlite Object
function Highlite(fullBox)
{
    this.fullBox = fullBox;
    this.scaledBox = new Box(0,0,0,0);
    this.img = document.createElement('img');
    this.img.className = 'highlite';
    this.img.src = ImageViewer.HIGHLITE_IMAGE;
    this.resize = resizeHighlite;
    this.position = positionHighlite;
}

function resizeHighlite(scaleFactor)
{
    this.scaledBox.width = Math.ceil(this.fullBox.width/scaleFactor);
    this.img.style.width = this.scaledBox.width+'px';
    this.scaledBox.height = Math.ceil(this.fullBox.height/scaleFactor);
    this.img.style.height = this.scaledBox.height+'px';

}

function positionHighlite(imageViewer, mouse, scaleFactor)
{
    this.scaledBox.x = (Math.ceil(this.fullBox.x/scaleFactor) + imageViewer.imageTileOffset.x + (mouse.x - imageViewer.start.x));
    this.img.style.left = this.scaledBox.x + 'px';
    this.scaledBox.y = (Math.ceil(this.fullBox.y/scaleFactor) + imageViewer.imageTileOffset.y + (mouse.y - imageViewer.start.y));
    this.img.style.top = this.scaledBox.y + 'px';

}
