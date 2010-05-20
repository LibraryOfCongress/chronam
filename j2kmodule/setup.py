# not sure why, but this seems to be key in order for it to run (else
# it builds but we get a j2k.so that's bigger and that gets relocated
# errors when trying to run against it)
# cp libawj2k.so.2.0.1 libawj2k.so  

# pfexec crle -u -l /opt/local/lib

# export LD_LIBRARY_PATH=/opt/csw/lib:/usr/ucblib


from distutils.core import setup, Extension
setup(name='j2k',
      version='1.0',
      ext_modules=[
        Extension('j2k', ['j2kmodule.c'],
                  include_dirs=['./include'],
                  libraries=['awj2k'])
        ],
      ),

