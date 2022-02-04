'''
Created on 23 May 2017

@author: Mats Vernersson, SMHI
'''
import matplotlib
matplotlib.use('Agg')

import h5py
import numpy as np
import pyproj
# import mpl_toolkits.basemap.pyproj as pyproj
import shutil

COMPRESSION = "gzip"
COMPRESSION_LEVEL = 6

class Where(object):
  def __init__(self, where_node=None,
               xscale=None, yscale=None, xsize=None, ysize=None,
               ul_lat=None, ul_lon=None, ur_lat=None, ur_lon=None,
               ll_lat=None, ll_lon=None, lr_lat=None, lr_lon=None,
               projdef=None):

    self.xscale = xscale
    self.yscale = yscale
    self.xsize = xsize
    self.ysize = ysize
    self.ul_lat = ul_lat
    self.ul_lon = ul_lon
    self.ur_lat = ur_lat
    self.ur_lon = ur_lon
    self.ll_lat = ll_lat
    self.ll_lon = ll_lon
    self.lr_lat = lr_lat
    self.lr_lon = lr_lon
    self.projdef = projdef

    if where_node is not None:
      if xscale is None:
        self.xscale = where_node.attrs.get('xscale',None)
      if yscale is None:
        self.yscale = where_node.attrs.get('yscale')
      if xsize is None:
        self.xsize = where_node.attrs.get('xsize')
      if ysize is None:
        self.ysize = where_node.attrs.get('ysize')
      if ul_lat is None:
        self.ul_lat = where_node.attrs.get('UL_lat')
      if ul_lon is None:
        self.ul_lon = where_node.attrs.get('UL_lon')
      if ur_lat is None:
        self.ur_lat = where_node.attrs.get('UR_lat')
      if ur_lon is None:
        self.ur_lon = where_node.attrs.get('UR_lon')
      if ll_lat is None:
        self.ll_lat = where_node.attrs.get('LL_lat')
      if ll_lon is None:
        self.ll_lon = where_node.attrs.get('LL_lon')
      if lr_lat is None:
        self.lr_lat = where_node.attrs.get('LR_lat')
      if lr_lon is None:
        self.lr_lon = where_node.attrs.get('LR_lon')
      if projdef is None:
        self.projdef = where_node.attrs.get('projdef')
        if isinstance(self.projdef, bytes):
            self.projdef = self.projdef.decode('UTF-8')

    self.min_lon = min([self.ul_lon, self.ur_lon, self.ll_lon, self.lr_lon])
    self.min_lat = min([self.ul_lat, self.ur_lat, self.ll_lat, self.lr_lat])
    self.max_lon = max([self.ul_lon, self.ur_lon, self.ll_lon, self.lr_lon])
    self.max_lat = max([self.ul_lat, self.ur_lat, self.ll_lat, self.lr_lat])

  def get_description(self):
    where_description = ""
    where_description += "projdef=" + str(self.projdef) + ", "
    where_description += "xscale=%.1f, "  % (self.xsize)
    where_description += "yscale=%.1f, "  % (self.xsize)
    where_description += "xsize=%.1f, "  % (self.xsize)
    where_description += "ysize=%.1f, "  % (self.xsize)
    where_description += "ul_lat=%.10f, " % (self.ul_lat)
    where_description += "ul_lon=%.10f, " % (self.ul_lon)
    where_description += "ur_lat=%.10f, " % (self.ur_lat)
    where_description += "ur_lon=%.10f, " % (self.ur_lon)
    where_description += "ll_lat=%.10f, " % (self.ll_lat)
    where_description += "ll_lon=%.10f, " % (self.ll_lon)
    where_description += "lr_lat=%.10f, " % (self.lr_lat)
    where_description += "lr_lon=%.10f" % (self.lr_lon)

    return where_description

class PolarWhere(object):
  def __init__(self, where_node=None, height=None, lat=None, lon=None,
        rstart=None, rscale=None, nrays=None, nbins=None):
    self.where_node = where_node
    self.height = height
    self.lat = lat
    self.lon = lon
    self.rstart = rstart
    self.rscale = rscale
    self.nrays = nrays
    self.nbins = nbins

    if isinstance(self.where_node, h5py.Group):
      if self.height is None:
        self.height = where_node.attrs.get('height')
      if self.lat is None:
        self.lat = where_node.attrs.get('lat')
      if self.lon is None:
        self.lon = where_node.attrs.get('lon')

  def set_geometry(self, nbins=None, nrays=None, rscale=None, rstart=None):
    self.rstart = rstart
    self.rscale = rscale
    self.nrays = nrays
    self.nbins = nbins

class Quantity(object):
  def __init__(self, dataset=None, group_path= None, value=None, quantity=None,
        gain=None, offset=None, nodata=None, undetect=None):
    self.dataset = dataset
    self.group_path = group_path
    self.value = value
    self.quantity = quantity
    self.gain = gain
    self.offset = offset
    self.nodata = nodata
    self.undetect = undetect
    self.file_path = None
    self.datetime = None
    self.task = None

    if isinstance(self.dataset, h5py.Group):
      if self.value is None:
        self.value = self.dataset['data'][()]    #instead of .value
      if self.quantity is None:
        self.quantity = self.dataset['what'].attrs.get('quantity')
      if self.gain is None:
        self.gain = self.dataset['what'].attrs.get('gain')
      if self.offset is None:
        self.offset = self.dataset['what'].attrs.get('offset')
      if self.nodata is None:
        self.nodata = self.dataset['what'].attrs.get('nodata')
      if self.undetect is None:
        self.undetect = self.dataset['what'].attrs.get('undetect')

    if isinstance(self.quantity, bytes):
      self.quantity = self.quantity.decode('UTF-8')

  def set_dataset_attributes(self, file_path=None, datetime=None, task=None):
    if file_path is not None:
      self.file_path = file_path
    if datetime is not None:
      self.datetime = datetime
    if task is not None:
      self.task = task

  def get_real_values(self):
    # TODO: Mask where no data! --> np.ma.masked_equal()
    if all(x is not None for x in (self.value, self.gain, self.offset)):
        return self.value * self.gain + self.offset
    else:
        return None

class OdimH5File(object):
  def __init__(self, filepath, writeable=False):
    self.writeable = writeable
    if writeable:
      mode = "r+"
    else:
      mode = "r"
    self.f = h5py.File(filepath, mode)   ##########

    self.odim_object = self.f['/what'].attrs.get('object')
    if isinstance(self.odim_object, bytes):
      self.odim_object = self.odim_object.decode('UTF-8')

    self.filepath = filepath

    self.polar = None

    if self.odim_object.lower() in ['scan', 'pvol']:
        self.where = PolarWhere(self.f['/where'])
        self.polar = True
    else:
        self.where = Where(self.f['/where'])
        self.proj = pyproj.Proj(str(self.where.projdef))
        self.polar = False

    # Projection plus corner compensation
    self.no_of_datasets = len([x for x in self.f.keys() if x.startswith("dataset")])

  def get_where_description(self):
    return self.where.get_description()

  def set_writeable(self):
    if not self.writeable:
      self.writeable = True
      mode = "r+"
      self.close()
      self.f = h5py.File(self.filepath, mode)

  def set_unwriteable(self):
    if self.writeable:
      self.writeable = False
      mode = "r"
      self.close()
      self.f = h5py.File(self.filepath, mode)

  def close(self):
    self.f.close()

  def get_ul_x_y(self):
    x, defined_y = self.proj(self.where.ul_lon, self.where.ul_lat)
    # due to a bug in Baltrad, the lon-lat values for UL, are located one 'pixel' above the corner. Thus we currently need to adjust to get correct position
    corrected_y = defined_y - self.where.yscale

    return x, corrected_y


  def get_attribute_from_dataset(self, elevation, attribute):
    group_path = self.get_first_datapath('elangle', elevation)
    ds = group_path.split('/')[0]
    return self.get_first_attribute_value_by_name(attribute, start_group=ds)


  def get_attribute_value(self, datapath, attribute_name):
    return self.f[datapath].attrs[attribute_name]

  def get_quantity(self, quantity, start_path=None):
    group_path = self.get_datasetpath_for_quantity(quantity, start_path=start_path)
    if group_path is None:
        print('WARNING: Quantity "%s" not found in file %s' % (quantity, self.filepath))
        return None
    # group_path = self.get_datasetpath_for_quantity(quantity, start_path)
    # print('get quantity, group path', group_path)
    if start_path is not None:
      dataset_path = '/'.join([start_path, group_path])
    else:
      dataset_path = group_path
    # Set geometry when polar dataset is known
    path_parts = dataset_path.split("/")
    parent_group_path = "/".join(path_parts[:-1])
    dataset = self.f[parent_group_path]
    if self.polar:
      nbins = dataset['where'].attrs.get('nbins')
      nrays = dataset['where'].attrs.get('nrays')
      rscale = dataset['where'].attrs.get('rscale')
      rstart = dataset['where'].attrs.get('rstart')
      self.where.set_geometry(nbins=nbins, nrays=nrays,
            rscale=rscale, rstart=rstart)
    return Quantity(self.f[dataset_path], group_path=dataset_path)

  def get_quantity_from_elevation(self, quantity, elevation):
    group_path = self.get_datasetpath_for_attribute("elangle", elevation)
    return self.get_quantity(quantity, group_path)

  def get_datafield(self, dataset_data_path):
    what_path = dataset_data_path + '/what'
    dataset = self.f[dataset_data_path + '/data']
    gain = self.f[what_path].attrs['gain']
    offset = self.f[what_path].attrs['offset']
    undetect = self.f[what_path].attrs['undetect']
    nodata = self.f[what_path].attrs['nodata']

    # Defining the lat-long grid vs x and y from the dataset
    ny_lats = dataset.shape[0]
    nx_lons = dataset.shape[1]

    # Initialization of dataset
    data_field = np.zeros((ny_lats, nx_lons))

    # Load the dataset into the data array
    dataset.read_direct(data_field)
    data_field_dummy = np.copy(data_field)
    
    #Set undetect to nan
    data_field[data_field_dummy==undetect]=np.nan
    data_field[data_field_dummy==nodata]=np.nan

    # Rescaling the "raw" radar data with gain and offset
    data_field = (data_field * gain) + offset
    
    return data_field
 
 

  def get_datasetpath_for_quantity(self, quantity_value, start_group=None,
        start_path=None, get_parent_group=False):
    if not start_group and start_path:
      start_group = self.f[start_path]
    # print('get datasetpath q, start_group', start_group)
    # print('get datasetpath q, start_path', start_path)
    return self.get_datasetpath_for_attribute("quantity", quantity_value,
            start_group, get_parent_group)

  def get_datasetpath_for_attribute(self, attribute, attr_value, start_group=None,
        get_parent_group=False):
    # FIXME: Should this return group node path? Currently. when looking for
    # FIXME: '/how/task' it will return '/', not '/how'
    # FIXME: The intention of get_parent_group=True was to get '/' above
    dataset_path = self.get_first_datapath(attribute, attr_value, start_group)
    # print('get datasetpath attr dataset_path', dataset_path)
    if not dataset_path:
      return None
    path_parts = dataset_path.split("/")
    if get_parent_group:
      trim = 2
    else:
      trim = 1
    if len(path_parts) > trim:
      self.current_dataset_path = "/".join(path_parts[:len(path_parts)-trim])
    else:
      self.current_dataset_path = "/"
    # print('current dataset path', self.current_dataset_path)
    return self.current_dataset_path

  def get_first_datapath(self, attribute, attr_value, start_group=None):
    if not isinstance(start_group, h5py.Group):
      start_group = self.f
    # print('get first datapath, start_group', start_group)
    self.current_attribute_name = attribute
    self.current_attribute_value = attr_value
    return start_group.visititems(self.find_attribute_with_value)

  def find_attribute_with_value(self, name, obj):
    obj_attrs_list = list(obj.attrs)
    # print(obj, name, self.current_attribute_name, self.current_attribute_value)
    obj_attr_value = obj.attrs.get(self.current_attribute_name)
    if isinstance(obj_attr_value, bytes):
      obj_attr_value = obj_attr_value.decode('UTF-8')
    if self.current_attribute_name in obj_attrs_list \
            and obj_attr_value == self.current_attribute_value:
      self.current_dataset_path = name
      return name
    else:
      return None

  def get_first_attribute_value_by_name(self, attribute, start_group=None):
    if isinstance(start_group, str):
      start_group = self.f[start_group]
    if not isinstance(start_group, h5py.Group):
      start_group = self.f
    self.current_attribute_name = attribute
    return start_group.visititems(self.find_attribute_by_name)

  def find_attribute_by_name(self, name, obj):
    obj_attr_value = obj.attrs.get(self.current_attribute_name)
    if isinstance(obj_attr_value, bytes):
      obj_attr_value = obj_attr_value.decode('UTF-8')
    return obj_attr_value

  def copy(self, target_filepath):
    shutil.copyfile(self.filepath, target_filepath)
    return OdimH5File(target_filepath)

  def add_dataset(self, parent_dataset_path=None):
    if parent_dataset_path:
      parent_dataset = self.f[parent_dataset_path]
      no_of_datafields = len([x for x in parent_dataset.keys() if x.startswith("data")])
      name = "data%i" % (no_of_datafields + 1)
      dataset_path = parent_dataset_path + "/" + name
    else:
      parent_dataset_path = ""
      parent_dataset = self.f
      name = "dataset%i" % (self.no_of_datasets + 1) # assumes all datasets are numbered in order without gaps
      self.no_of_datasets += 1
      dataset_path = name
    parent_dataset.create_group(name)
    return dataset_path

  def create_groups_if_nonexistent(self, path):
    if not path in self.f:
      _ = self.f.create_group(path)

  def set_datafield(self, datapath, data):
    full_data_path = datapath + "/data"
    if full_data_path in self.f:
      del self.f[full_data_path]
    self.f[datapath].create_dataset("data", data=data, compression=COMPRESSION, compression_opts=COMPRESSION_LEVEL)

  def copy_datagroup(self, source_path, target_path, group_name):
    full_source_path = source_path + "/" + group_name
    self.f.copy(self.f[full_source_path], self.f[target_path])
    return target_path + "/" + group_name

  def set_attribute(self, path, attribute_name, attribute_value):
    self.create_groups_if_nonexistent(path)
    if isinstance(attribute_value, str):
        self.f[path].attrs.create(attribute_name, np.string_(attribute_value))
    else:
        self.f[path].attrs.__setitem__(attribute_name, attribute_value)

  def update_datafield_data(self, dataset_data_path, new_data):
    self.f[dataset_data_path + '/data'].write_direct(new_data)

def create_where_from_description_string(description_string):
  xscale = None
  yscale = None
  xsize = None
  ysize = None
  ul_lat = None
  ul_lon = None
  ur_lat = None
  ur_lon = None
  ll_lat = None
  ll_lon = None
  lr_lat = None
  lr_lon = None
  projdef = None

  where_parts = description_string.split(", ")
  for part in where_parts:
    if part.startswith("xscale"):
      xscale = float(part.split("=")[1])
    elif part.startswith("yscale"):
      yscale = float(part.split("=")[1])
    elif part.startswith("xsize"):
      xsize = float(part.split("=")[1])
    elif part.startswith("ysize"):
      ysize = float(part.split("=")[1])
    elif part.startswith("ul_lat"):
      ul_lat = float(part.split("=")[1])
    elif part.startswith("ul_lon"):
      ul_lon = float(part.split("=")[1])
    elif part.startswith("ur_lat"):
      ur_lat = float(part.split("=")[1])
    elif part.startswith("ur_lon"):
      ur_lon = float(part.split("=")[1])
    elif part.startswith("ll_lat"):
      ll_lat = float(part.split("=")[1])
    elif part.startswith("ll_lon"):
      ll_lon = float(part.split("=")[1])
    elif part.startswith("lr_lat"):
      lr_lat = float(part.split("=")[1])
    elif part.startswith("lr_lon"):
      lr_lon = float(part.split("=")[1])
    elif part.startswith("projdef"):
      projdef = part.split("projdef=")[1]

  return Where(where_node=None, xscale=xscale, yscale=yscale, xsize=xsize, ysize=ysize,
               ul_lat=ul_lat, ul_lon=ul_lon, ur_lat=ur_lat, ur_lon=ur_lon, ll_lat=ll_lat,
               ll_lon=ll_lon, lr_lat=lr_lat, lr_lon=lr_lon, projdef=projdef)
