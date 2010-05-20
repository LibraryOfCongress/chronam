import os
import j2k
import Image

from StringIO import StringIO

from django.test import TestCase

from chronam.settings import STORAGE

JP2_PATH = "dlc/batch_dlc_jamaica_ver01/data/sn83030214/00175039259/0001.jp2"


class JP2Test(TestCase):

    def test_raw_image(self):
        filename = os.path.join(STORAGE, JP2_PATH)

        rows, cols, nChannels, bpp, data = j2k.raw_image(filename, 300, 300)

        im = Image.frombuffer("L", (cols, rows), data, "raw", "L", 0, 1)

        sio = StringIO()
        im.thumbnail((200, 265), Image.ANTIALIAS)
        im.save(sio, "JPEG")
        self.assertTrue(sio.getvalue())
        

    def test_image_tile_raw(self):
        filename = os.path.join(STORAGE, JP2_PATH)

        width, height = 640, 480
        rows, cols, nChannels, bpp, data = j2k.image_tile_raw(filename, width, height, 0, 0, 2*width, 2*height)


        im = Image.frombuffer("L", (cols, rows), data, "raw", "L", 0, 1)

        sio = StringIO()
        im = im.resize((width, height), Image.ANTIALIAS) 
        im.save(sio, "JPEG")

        self.assertTrue(sio.getvalue())
        
    def test_dimensions(self):
        filename = os.path.join(STORAGE, JP2_PATH)

        width, height = j2k.dimensions(filename)
        self.assertEqual((width, height), (6378, 8724))

