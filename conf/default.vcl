# new 4.0 format.
vcl 4.0;

import directors;

backend app1 {
    .host = "ndnpappvlp01.loc.gov";
    .connect_timeout = 15s;
    .first_byte_timeout = 120s;
    .between_bytes_timeout = 120s;
}

backend app2 {
    .host = "ndnpappvlp02.loc.gov";
    .connect_timeout = 15s;
    .first_byte_timeout = 120s;
    .between_bytes_timeout = 120s;
}

#create a virtual group for use when we do the load balancing
sub vcl_init {
    new app = directors.hash();
    app.add_backend(app1, 1);
    app.add_backend(app2, 1);
}

#stream all files, otherwise you have to wait for e.g. an entire PDF or JP2, etc. to be saved into the cache before Varnish will send the first byte to the client
sub vcl_backend_response {
    set beresp.do_stream = true;
    set beresp.grace = 1h;
    if (beresp.http.content-type ~ "(text|application)") {
        set beresp.do_gzip = true;
    }
}

sub vcl_recv {
    #all requests come through the Netscaler
    if (req.http.CF-Connecting-IP) {
        set req.http.X-Forwarded-For = req.http.CF-Connecting-IP;
    }
    else{
        set req.http.X-Forwarded-For = req.http.X-ACE-Forwarded-For;
    }

    #load balance by the user's ip address
    set req.backend_hint = app.backend(req.http.X-Forwarded-For);

    #Varnish's default configuration won't cache requests with cookies since that's commonly used for login systems which alter the page contents – see https://www.varnish-cache.org/docs/trunk/users-guide/increasing-your-hitrate.html#cookies
    if (req.http.cookie) {
        unset req.http.cookie;
    }

    #don't cache or modify /data or any pdf files
    if (req.url ~ "^/data/") {
        return (pass);
    }
    if (req.url ~ "\.pdf$") {
        return (pass);
    }
}

#prefer a fresh object, but when one cannot be found Varnish will look for stale one. This replaces req.grace in vcl_recv()
sub vcl_hit {
    if (obj.ttl >= 0s) {
       return (deliver);
    }
    if (obj.ttl + obj.grace > 0s) {
        return (deliver);
    }
    return (fetch);
}

#Preserve any Vary headers from the backend but ensure that Vary always includes Accept-Encoding since we enable gzip transfer encoding
sub vcl_deliver {
    if (!resp.http.Vary) {
        set resp.http.Vary = "Accept-Encoding";
    } else if (resp.http.Vary !~ "(?i)Accept-Encoding") {
        set resp.http.Vary = resp.http.Vary + ",Accept-Encoding";
    }
}

#TODO but we should probably use a standard LC error page or confirm that CloudFlare will substitute the nice P1 error page for a backend 5xx error
sub vcl_backend_error {
    set beresp.http.Content-Type = "text/html; charset=utf-8";
    set beresp.http.Retry-After = "5";
    synthetic ({"
<!DOCTYPE html>
    <html>
        <head>
            <title>The page is temporarily unavailable</title>
        </head>
    <body>
         <h1>Chronicling America is currently unavailable</h1>
             <p>The Chronicling America website is currently offline, undergoing maintenance.  We regret the inconvenience, and invite you to visit other collections available on the Library of Congress website at <a href="http://www.loc.gov">www.loc.gov</a> while we are working to restore service.</p>
    </body>
</html>
"});

    return (deliver);
}
