import _j2k


def raw_image(filename, width, height):
    return _j2k.raw_image(filename, width, height)
    

def image_tile(filename, width, height, x1, y1, x2, y2):
    return _j2k.image_tile(filename, width, height, x1, y1, x2, y2)


def image_tile_raw(filename, width, height, x1, y1, x2, y2):
    return _j2k.image_tile_raw(filename, width, height, x1, y1, x2, y2)


def dimensions(filename):
    return _j2k.dimensions(filename)

