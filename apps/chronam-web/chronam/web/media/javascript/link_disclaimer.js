function LinkDisclaimer(disclaimerUrl)
{
	this.disclaimerUrl = disclaimerUrl;
	
	// Use the more appropriate function if its available.
	this.encode = window.encodeURI? window.encodeURI : escape;	
	
	this.rewriteAnchor =
	function(anchorElement)
	{
		anchorElement.href = this.disclaimerUrl + this.encode(anchorElement.href);
		anchorElement.onmouseup = "";
		return true;
	}
}
