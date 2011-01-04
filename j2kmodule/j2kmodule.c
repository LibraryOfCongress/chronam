#include <Python.h>

#include "j2k.h"
#include "aw_j2k_errors.h"

static PyObject *J2KError;


#define Malloc malloc

#define RETURN_IF_ERR(retval, error_message)   \
  if (retval) {                                \
    PyErr_SetString(J2KError, error_message);  \
    return NULL;                               \
  }

static int MAX_PROGRESSION_LEVEL = 6;   

static double scaled_dimension(int progression_level, int dimension) {
  int scale_factor = 2<<(progression_level-1); 
  return (double)dimension / (double)scale_factor;
}

/**
 * Find the progression level that produces an images larger than or
 * equal to requested image
 */
static int desired_progression_level(int x1, int x2, int y1, int y2, 
                                     int width, int height) {
  int level = MAX_PROGRESSION_LEVEL;
  while (level > 1 && 
         width > scaled_dimension(level, x2-x1) && 
         height > scaled_dimension(level, y2-y1)) {
    level--;
  }
  //fprintf(stderr, "level `%d'\n", level);
  return level;
}

static BYTE *
load_raw_data(char *filename, unsigned long *length)
{
  FILE *fp;
  BYTE *data;

  fp = fopen(filename, "rb");
  if (!fp) {
    fprintf(stderr, "Warning: unable to open file `%s' for reading\n",
            filename);
    *length = 0;
    return NULL;
  }

  fseek(fp, 0, SEEK_END);
  *length = ftell(fp);
  rewind(fp);

  data = (BYTE *)Malloc(sizeof(BYTE) * (*length));
  fread(data, 1, *length, fp);
  fclose(fp);
  return data;
}

static PyObject *
get_output_image(aw_j2k_object *j2k_object)
{
  PyObject * result;
  int retval;
  unsigned char *image_buffer;
  unsigned long int image_buffer_length;

  image_buffer = NULL;
  retval = aw_j2k_get_output_image(j2k_object, &image_buffer,
                                   &image_buffer_length);
  RETURN_IF_ERR(retval, "aw_j2k_get_output_image returned an error code.")
  result = Py_BuildValue("s#", image_buffer, image_buffer_length);
  aw_j2k_free(j2k_object, image_buffer);
  return result;
}

static int FULL_XFORM_FLAG = 0;

static PyObject * 
j2k_image_tile(PyObject *self, PyObject *args) 	 	 
{ 	 	 
  unsigned char* buffer;
  unsigned long buffer_length;
  char *filename;
  int width, height, x1, y1, x2, y2;
  PyObject * result;
  aw_j2k_object *j2k_object;
  int retval;
  //long int quality = 75;

  if (!PyArg_ParseTuple(args, "siiiiii", &filename,
                        &width, &height, &x1, &y1, &x2, &y2))
    return NULL;

  j2k_object = NULL;
  retval = aw_j2k_create(&j2k_object);
  RETURN_IF_ERR(retval, "aw_j2k_create returned an error code.");

  buffer = load_raw_data(filename, &buffer_length);
  retval = aw_j2k_set_input_image(j2k_object, buffer, buffer_length);
  RETURN_IF_ERR(retval, "aw_j2k_set_input_image returned an error code.");
  free(buffer);

  retval = aw_j2k_set_input_j2k_resolution_level(j2k_object, 
                 desired_progression_level(x1, x2, y1, y2, width, height),
                                                 FULL_XFORM_FLAG);
  RETURN_IF_ERR(retval, "aw_j2k_set_input_j2k_resolution_level returned an error code.");

  //retval = aw_j2k_set_input_j2k_quality_level(j2k_object, ??);

  retval = aw_j2k_set_input_j2k_region_level(j2k_object, x1, y1, x2, y2);
  RETURN_IF_ERR(retval,
                "aw_j2k_set_input_j2k_region_level returned an error code.");

  retval = aw_j2k_set_output_type(j2k_object, AW_J2K_FORMAT_JPG);
  RETURN_IF_ERR(retval, "aw_j2k_set_output_type returned an error code.");

  //retval = aw_j2k_set_output_jpg_options(j2k_object, quality);
  //RETURN_IF_ERR(retval, "aw_j2k_set_output_jpg_options returned error code.");

  retval = aw_j2k_set_output_com_image_size(j2k_object, height, width,
                                            AW_J2K_PRESERVE_ASPECT_RATIO_NO_PAD);
  RETURN_IF_ERR(retval, "aw_j2k_set_output_com_image_size returned an error code.");

  result = get_output_image(j2k_object);

  retval = aw_j2k_destroy(j2k_object);
  j2k_object = NULL;
  RETURN_IF_ERR(retval, "aw_j2k_destroy returned an error code.");

  return result;
} 

static PyObject *
j2k_image_tile_raw(PyObject *self, PyObject *args)
{
  unsigned char* buffer;
  unsigned long buffer_length;
  char *filename;
  int width, height, x1, y1, x2, y2;
  PyObject * result;
  aw_j2k_object *j2k_object;
  int retval;

  unsigned char *image_buffer;
  unsigned long int image_buffer_length;
  unsigned long int rows, cols, nChannels, bpp;

  image_buffer = NULL;

  if (!PyArg_ParseTuple(args, "siiiiii", &filename,
                        &width, &height, &x1, &y1, &x2, &y2))
    return NULL;

  j2k_object = NULL;
  retval = aw_j2k_create(&j2k_object);
  RETURN_IF_ERR(retval, "aw_j2k_create returned an error code.");

  buffer = load_raw_data(filename, &buffer_length);
  retval = aw_j2k_set_input_image(j2k_object, buffer, buffer_length);
  RETURN_IF_ERR(retval, "aw_j2k_set_input_image returned an error code.");
  free(buffer);

  retval = aw_j2k_set_input_j2k_resolution_level(j2k_object, 
                 desired_progression_level(x1, x2, y1, y2, width, height),
                                                 FULL_XFORM_FLAG);
  RETURN_IF_ERR(retval, "aw_j2k_set_input_j2k_resolution_level returned an error code.");

  //retval = aw_j2k_set_input_j2k_quality_level(j2k_object, ??);

  retval = aw_j2k_set_input_j2k_region_level(j2k_object, x1, y1, x2, y2);
  RETURN_IF_ERR(retval, 
                "aw_j2k_set_input_j2k_region_level returned an error code.");

  retval = aw_j2k_set_output_com_image_size(j2k_object, height, width, 
                                            AW_J2K_PRESERVE_ASPECT_RATIO_NO_PAD);

  aw_j2k_get_output_image_raw(j2k_object,
                              &image_buffer, &image_buffer_length,
                             &rows, &cols,
                             &nChannels,
                              &bpp, 0);

  result = Py_BuildValue("iiiis#", rows, cols, nChannels, bpp,
                         image_buffer, image_buffer_length);

  aw_j2k_free(j2k_object, image_buffer);
  aw_j2k_destroy(j2k_object);
  j2k_object = NULL;
  return result;
}


static PyObject *
j2k_raw_image(PyObject *self, PyObject *args)
{
  unsigned char *buffer;
  unsigned long buffer_length;
  char *filename;
  int width, height;
  PyObject * result;
  aw_j2k_object *j2k_object;

  unsigned char *image_buffer;
  unsigned long int image_buffer_length;
  unsigned long int rows, cols, nChannels, bpp;

  image_buffer = NULL;

  if (!PyArg_ParseTuple(args, "sii", &filename,
                        &width, &height))
    return NULL;

  j2k_object = NULL;
  aw_j2k_create(&j2k_object);
  buffer = load_raw_data(filename, &buffer_length);
  aw_j2k_set_input_image(j2k_object, buffer, buffer_length);
  free(buffer);

  aw_j2k_set_output_com_image_size(j2k_object, height, width,
                                   AW_J2K_PRESERVE_ASPECT_RATIO_NO_PAD);

  aw_j2k_get_output_image_raw(j2k_object,
                              &image_buffer, &image_buffer_length,
                             &rows, &cols,
                             &nChannels,
                              &bpp, 0);

  result = Py_BuildValue("iiiis#", rows, cols, nChannels, bpp,
                         image_buffer, image_buffer_length);

  aw_j2k_free(j2k_object, image_buffer);
  aw_j2k_destroy(j2k_object);
  j2k_object = NULL;
  return result;
}


static PyObject *
j2k_dimensions(PyObject *self, PyObject *args)
{
  unsigned char *buffer;
  unsigned long buffer_length;
  char *filename;
  PyObject * result;
  aw_j2k_object *j2k_object;

  unsigned long int rows, cols, nChannels, bpp;


  if (!PyArg_ParseTuple(args, "s", &filename))
    return NULL;

  j2k_object = NULL;
  aw_j2k_create(&j2k_object);
  buffer = load_raw_data(filename, &buffer_length);
  aw_j2k_set_input_image(j2k_object, buffer, buffer_length);
  free(buffer);


  /* find out the size of the image */ 
  aw_j2k_get_input_image_info(j2k_object, &rows, &cols, &bpp, 
                              &nChannels); 

  result = Py_BuildValue("ii", rows, cols);

  aw_j2k_destroy(j2k_object);
  j2k_object = NULL;
  return result;
}




static PyMethodDef J2KMethods[] = {
    {"image_tile",  j2k_image_tile, METH_VARARGS,
     "load a jp2, crop, resize and output as jpg."}, 
    {"image_tile_raw",  j2k_image_tile_raw, METH_VARARGS,
     "load a jp2, crop and output as raw."},
    {"raw_image",  j2k_raw_image, METH_VARARGS,
     "load a jp2 and output the raw image."},
    {"dimensions",  j2k_dimensions, METH_VARARGS,
     "returns the dimensions of the jp2"},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC
init_j2k(void)
{
  PyObject *m;

  m = Py_InitModule("_j2k", J2KMethods);
  if (m == NULL)
    return;

  J2KError = PyErr_NewException("j2k.error", NULL, NULL);
  Py_INCREF(J2KError);
  PyModule_AddObject(m, "error", J2KError);
}
