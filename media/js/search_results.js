function setUrlVar(name, val){
    index = location.href.indexOf('?')
    
    var base_url = index != -1 ? location.href.slice(0, index+1) : location.href + '?';
    var found = false;
    if (index != -1){
        var hashes = location.href.slice(index+1).split('&');
        for(var i = 0; i < hashes.length; i++)
        {
           if (hashes[i].length > 0) {
               hash = hashes[i].split('=');
               if (hash[0] == name){
                 base_url = base_url + hash[0] + '=' + val + '&';
                 found = true;
               } else {
                 base_url = base_url + hash[0] + '=' + hash[1] + '&';
               }
           }
       }
   }
   if (found == false){
       base_url = base_url + name + '=' + val;
   }
   if (base_url.charAt(base_url.length - 1) == '&') {
       base_url = base_url.slice(0, base_url.length-1)
   }
   return base_url;
}; 