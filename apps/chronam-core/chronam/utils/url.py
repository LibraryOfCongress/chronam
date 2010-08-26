def pack_url_path(url):
    if url == None:
        return 'none'
    url = url.lower()
    url = url.replace(' ', '_')
    return url

def unpack_url_path(url):
    if url == 'none':
        return None
    url = url.replace('_', ' ')
    return url
