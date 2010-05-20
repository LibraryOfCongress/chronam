def pack_url_path(url):
    if url == None:
        return 'none'
    url = url.lower()
    url = url.replace(' ', '_')
    url = url.replace('.', '')
    return url

def unpack_url_path(url):
    if url == 'none':
        return None
    url = url.replace('_', ' ')
    url = ' '.join(x.capitalize() for x in url.split())
    return url
