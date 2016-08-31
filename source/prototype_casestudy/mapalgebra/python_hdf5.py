import h5py
import math
import numpy


class lue_h5py(object):

    """ accessor to a lue hdf file. fields and partly agents """

    def __init__(self, filename):

        self._hdf_ref = h5py.File(
            filename, "r+", driver="core", backing_store=True)

    def close_current_hdf5_file(self):
        self._hdf_ref.close()

    def get_property_value(self, _name_phenomenon, _name_property_set,
                            _name_property, timestep=-1):
        """ Returns the most recent value """
        # get the current time step

        self._property_exists(
            _name_phenomenon, _name_property_set, _name_property)

        if timestep < 0:
            ts_nr = self._current_timestep(
                _name_phenomenon, _name_property_set, _name_property)
            ts_idx = ts_nr - 1
        else:
            ts_idx = timestep

        if self.is_field(_name_phenomenon, _name_property_set, _name_property):
            var = self.get_property_set_prop(
                _name_phenomenon, _name_property_set, _name_property
                ).get("value/0/")
        else:
            var = self.get_property_set_prop(
                _name_phenomenon, _name_property_set, _name_property
                ).get("value")

        return var[ts_idx]

    def set_property_value(self, _name_phenomenon, _name_property_set,
                            _name_property, value):
        """ Sets the most recent value """
        # get the current time step
        self._property_exists(
            _name_phenomenon, _name_property_set, _name_property)

        ts_nr = self._current_timestep(
            _name_phenomenon, _name_property_set, _name_property)

        if self.is_field(_name_phenomenon, _name_property_set, _name_property):
            data = self._get_ref_property_value(
                _name_phenomenon, _name_property_set, _name_property
                ).get("value/0/")
            data.resize((data.shape[0] + 1, data.shape[1], data.shape[2]))
        else:
            data = self._get_ref_property_value(
                _name_phenomenon, _name_property_set, _name_property
                ).get("value")
            data.resize((data.shape[0] + 1, data.shape[1]))

        data[ts_nr] = value

    def _update_time_domain_for_properties(self, _name_phenomenon,
                                           _name_property_set, timestep):
        properties = self.list_property_sets_prop(
            _name_phenomenon, _name_property_set)

        for p in properties:
            self._get_ref_property_value(_name_phenomenon,
                                         _name_property_set, p).get(
                "time discretization/value")[:] = timestep

    def update_time_domain(self, _name_phenomenon, _name_property_set,
                           timestep):
        """ updates the nr of timesteps in the domain (use at the end of the \
        dynamic section...) """

        ts = timestep + 1  # a slice 0 exists...
        self._update_time_domain(_name_phenomenon, _name_property_set, ts)

        # also update all time discretizations of properties
        self._update_time_domain_for_properties(
            _name_phenomenon, _name_property_set, ts)

    def _update_time_domain(self, phenomena, property_set, timesteps):
        #
        data = self.get_property_set(
            phenomena, property_set).get("domain/time/item")

        data[0] = data[0][0], (timesteps,)

    def current_timestep(self, _name_phenomenon, _name_property_set):

        path = "/phenomena/{0}/property_sets/{1}/properties/time discretization/value".format(
            _name_phenomenon, _name_property_set)
        current_timestep = self._hdf_ref.get(path)[0, 0]
        return current_timestep

    def _current_timestep(self, _name_phenomenon, _name_property_set,
                          _name_property):

        self._property_exists(
            _name_phenomenon, _name_property_set, _name_property)

        path = "/phenomena/{0}/property_sets/{1}/properties/{2}/time discretization/value".format(
            _name_phenomenon, _name_property_set, _name_property)
        current_timestep = self._hdf_ref.get(path)[0, 0]
        return current_timestep

    def list_phenomena(self):
        """ Returns list of phenomenon names """
        # later on, do not return keys each time...
        return self._hdf_ref.get("/phenomena/").keys()

    def get_property_set_prop(self, _name_phenomenon, _name_property_set,
                              _name_property):

        self._property_exists(
            _name_phenomenon, _name_property_set, _name_property)

        path = "/phenomena/{0}/property_sets/{1}/properties/{2}/".format(
            _name_phenomenon, _name_property_set, _name_property)
        return self._hdf_ref.get(path)

    def get_phenomenon(self, name):
        # returns ref to phenomenon
        self._phenomenon_exits(name)
        path = "/phenomena/{0}/".format(name)
        return self._hdf_ref.get(path)

    def _phenomenon_exits(self, name):
        if name in self.list_phenomena():
            return
        else:
            msg = "Could not find phenomenon '{0}'".format(name)
            raise ValueError(msg)

    def _get_ref_property_value(self, _name_phenomenon, _name_property_set,
                                 _name_property):
        path = "/phenomena/{0}/property_sets/{1}/properties/{2}/".format(
            _name_phenomenon, _name_property_set, _name_property)
        return self._hdf_ref.get(path)

    def list_property_sets(self, _name_phenomenon):
        return self.get_phenomenon(_name_phenomenon).get("property_sets/"
                                                         ).keys()

    def list_property_sets_prop(self, _name_phenomenon, _name_property_set):
        """ Returns list of  """
        # later on, do not return keys each time...

        values = self.get_property_set(
            _name_phenomenon, _name_property_set).get("properties/").keys()

        # remove 'keywords'
        if "space discretization" in values:
            values.remove("space discretization")

        if "time discretization" in values:
            values.remove("time discretization")

        return values

    def get_property_set(self, phenomenon_name, property_set):
        # returns ref to phenomenon
        self._property_set_exists(phenomenon_name, property_set)
        path = "/phenomena/{0}/property_sets/{1}/".format(
            phenomenon_name, property_set)
        return self._hdf_ref.get(path)

    def _property_set_exists(self, phenomenon_name, property_set_name):
        if property_set_name in self.list_property_sets(phenomenon_name):
            return
        else:
            msg = "Could not find property_set '{0}' in phenomenon '{1}'".\
            format(property_set_name, phenomenon_name)
            raise ValueError(msg)

    def get_cell_value_rc(self, _name_phenomenon, _name_property_set,
                          _name_property, row_nr, col_nr):
        """ Returns the the most recent cell value for row/column """
        self._property_exists(
            _name_phenomenon, _name_property_set, _name_property)

        if not self.is_field(_name_phenomenon, _name_property_set,
                             _name_property):
            return None

        # assume modeller provides row/col starting from 1
        row_idx = row_nr - 1
        col_idx = col_nr - 1

        data = self.get_property_value(
            _name_phenomenon, _name_property_set, _name_property)

        return data[row_idx, col_idx]

    def set_cell_value_rc(self, _name_phenomenon, _name_property_set,
                          _name_property, row_nr, col_nr, value):
        """ Sets the cell value of the most recent  """
        # assume modeller provides row/col starting from 1
        self._property_exists(
            _name_phenomenon, _name_property_set, _name_property)

        if not self.is_field(_name_phenomenon, _name_property_set,
                              _name_property):
            return

        row_idx = row_nr - 1
        col_idx = col_nr - 1

        ts_nr = self._current_timestep(
            _name_phenomenon, _name_property_set, _name_property)
        ts_idx = ts_nr - 1

        data = self._get_ref_property_value(
            _name_phenomenon, _name_property_set, _name_property).get(
                                                        "value/0/")
        data[ts_idx, row_idx, col_idx] = value

    def _nr_rows_columns(self, _name_phenomenon, _name_property_set,
                         _name_property, timestep=0):
        # returns number of rows and columns
        self._property_exists(
            _name_phenomenon, _name_property_set, _name_property)

        values = self.get_property_set(_name_phenomenon,
                                       _name_property_set).get(
            "properties/{0}/space discretization/value/".format(
                                        _name_property))

        return values[0, 0], values[0, 1]

    def cell_size(self, _name_phenomenon, _name_property_set, _name_property,
                  axis=0, timestep=0):
        """  Returns cellsize of a field property; None for agents """
        # return cell size along axis
        # 0 row
        # others not implemented; no timestep
        self._property_exists(
            _name_phenomenon, _name_property_set, _name_property)

        if not self.is_field(_name_phenomenon, _name_property_set,
                             _name_property):
            return None

        xmin, ymin, xmax, ymax = self.get_spatial_extent(
            _name_phenomenon, _name_property_set, _name_property)

        nr_rows, nr_cols = self._nr_rows_columns(
            _name_phenomenon, _name_property_set, _name_property, timestep)

        cell_size = (xmax - xmin) / nr_cols

        return cell_size

    # toegevoegd om zonder property het domein op te vragen op basis van
    # property set
    def get_spatial_extent_pset(self, _name_phenomenon, _name_property_set,
                                timestep=0):
        """ Returnx xmin, ymin  xmax, ymax for a field"""
        # field does not move atm

        data = self.get_property_set(
            _name_phenomenon, _name_property_set).get("domain/space/item")
        # xmin, ymin  xmax, ymax
        # convert to PCRaster still required somewhere... (upper left) ?

        if data is None:
            return None
        else:
            return data[0][0][0], data[0][0][1], data[0][1][0], data[0][1][1]

    def get_spatial_extent(self, _name_phenomenon, _name_property_set,
                           _name_property, timestep=0):
        """ Returnx xmin, ymin  xmax, ymax for a field"""
        # field does not move atm

        data = self.get_property_set(
            _name_phenomenon, _name_property_set).get("domain/space/item")
        # xmin, ymin  xmax, ymax
        # convert to PCRaster still required somewhere... (upper left) ?

        if data is None:
            return None
        else:
            return data[0][0][0], data[0][0][1], data[0][1][0], data[0][1][1]

    def is_field(self, _name_phenomenon, _name_property_set, _name_property):
        """ Returns true if property is a field; based on a simple check... """

        data = self.get_property_set(_name_phenomenon, _name_property_set).get(
            "properties/{0}/space discretization".format(_name_property))

        if data is None:
            return False
        else:
            return True

    def is_field_pset(self, _name_phenomenon, _name_property_set):
        """ Returns true if property is a field; based on a simple check... """

        data = self.get_property_set(_name_phenomenon, _name_property_set).get(
            "properties/space discretization")

        if data is None:
            return False
        else:
            return True

    def nr_items(self, _name_phenomenon, _name_property_set):
        """ Returns the number of items in a property set """
        data = self.get_property_set(
            _name_phenomenon, _name_property_set).get("domain/item")

        return data.shape[0]

    def item_ids(self, _name_phenomenon, _name_property_set):
        """ Returns the item ids in a phenomenon/property set """
        data = self.get_property_set(
            _name_phenomenon, _name_property_set).get("domain/item")

        return data[:]

    def nr_rows(self, _name_phenomenon, _name_property_set, _name_property):
        """ Returns number of rows of a property """
        self._property_exists(
            _name_phenomenon, _name_property_set, _name_property)

        if self.is_field(_name_phenomenon, _name_property_set, _name_property):
            return self._nr_rows_columns(_name_phenomenon, _name_property_set,
                                         _name_property)[0]
        else:
            return None

    def nr_cols(self, _name_phenomenon, _name_property_set, _name_property):
        """  Returns number of rows of a property """
        self._property_exists(
            _name_phenomenon, _name_property_set, _name_property)

        if self.is_field(_name_phenomenon, _name_property_set, _name_property):
            return self._nr_rows_columns(_name_phenomenon, _name_property_set,
                                          _name_property)[1]
        else:
            return None

    def get_cell_value_xy(self, _name_phenomenon, _name_property_set,
                          _name_property, xcoord, ycoord):
        """ Returns current cell value for coordinates """
        self._property_exists(
            _name_phenomenon, _name_property_set, _name_property)

        if not self.is_field(_name_phenomenon, _name_property_set,
                             _name_property):
            return

        ts_nr = self._current_timestep(
            _name_phenomenon, _name_property_set, _name_property)
        ts_idx = ts_nr - 1

        # todo error checking here
        row_idx, col_idx = self._coords_to_map_indices(
            _name_phenomenon, _name_property_set, _name_property, xcoord,
            ycoord, ts_idx)

        # assume modeller needs to provides row/col starting from 1
        row_nr = row_idx + 1
        col_nr = col_idx + 1

        return self.get_cell_value_rc(_name_phenomenon, _name_property_set,
                                      _name_property, row_nr, col_nr)

    def _coords_to_map_indices(self, _name_phenomenon, _name_property_set,
                               _name_property, xcoord, ycoord, timestep):

        xmin, ymin, xmax, ymax = self.get_spatial_extent(
            _name_phenomenon, _name_property_set, _name_property, timestep)

        west = xmin
        north = ymax
        cellSize = self.cell_size(
            _name_phenomenon, _name_property_set, _name_property, 0, timestep)

        xCol = (xcoord - west) / cellSize
        yRow = (north - ycoord) / cellSize

        row_idx = int(math.floor(yRow))
        col_idx = int(math.floor(xCol))

        nr_rows = int(math.floor((ymax - ymin) / cellSize))
        nr_cols = int(math.floor((xmax - xmin) / cellSize))

        if (col_idx + 1) > nr_cols:
            msg = "Column index ({0}) out of range (from 1 to {1}))".format(
                col_idx + 1, nr_cols)
            raise ValueError(msg)

        if (row_idx + 1) > nr_rows:
            msg = "Row index ({0}) out of range (from 1 to {1})".format(
                row_idx + 1, nr_rows)
            raise ValueError(msg)

        return row_idx, col_idx

    def set_cell_value_xy(self, _name_phenomenon, _name_property_set,
                           _name_property, xcoord, ycoord, value):
        """ Sets the current cell value for coordinates """
        self._property_exists(
            _name_phenomenon, _name_property_set, _name_property)

        if not self.is_field(_name_phenomenon, _name_property_set,
                             _name_property):
            return

        # todo error checking here
        row_idx, col_idx = self._coords_to_map_indices(
            _name_phenomenon, _name_property_set, _name_property, xcoord,
             ycoord, 0)

        # assume modeller needs to provides row/col starting from 1
        row_nr = row_idx + 1
        col_nr = col_idx + 1

        self.set_cell_value_rc(
            _name_phenomenon, _name_property_set, _name_property, row_nr,
            col_nr, value)

    def get_locations(self, _name_phenomenon, _name_property_set,
                      _name_property, timestep=-1):
        """ Returns list of tuples (x,y locations) for agents for the latest \
        time step; None for fields """
        self._property_exists(
            _name_phenomenon, _name_property_set, _name_property)

        if self.is_field(_name_phenomenon, _name_property_set, _name_property):
            return None

        if timestep < 0:
            ts_nr = self._current_timestep(
                _name_phenomenon, _name_property_set, _name_property)
            ts_idx = ts_nr - 1
        else:
            ts_idx = timestep

        data = self.get_property_set(
            _name_phenomenon, _name_property_set).get("domain/space/item")

        return data[ts_idx]

    def set_locations(self, _name_phenomenon, _name_property_set,
                      _name_property, values):
        """ Set list of tuples (x,y locations) for agents for the latest time \
        step; None for fields """
        self._property_exists(
            _name_phenomenon, _name_property_set, _name_property)

        ts_nr = self._current_timestep(
            _name_phenomenon, _name_property_set, _name_property)
        data = self.get_property_set(
            _name_phenomenon, _name_property_set).get("domain/space/item")

        if self.is_field_pset(_name_phenomenon, _name_property_set):
            return None

        data.resize((data.shape[0] + 1, data.shape[1]))

        data[ts_nr] = values

    def add_property(self, _name_phenomenon, _name_property_set, name, values):
        """ adds a 1d property """
        properties = self.get_property_set(
            _name_phenomenon, _name_property_set).get("properties")

        try:
            # Obtain the number of timesteps
            prop = self.list_property_sets_prop(
                _name_phenomenon, _name_property_set)
            timesteps = self._current_timestep(
                _name_phenomenon, _name_property_set, prop[0])

            prop = properties.create_group(name)

            if self.is_field_pset(_name_phenomenon, _name_property_set):
                prop_val = prop.create_group("value")
                prop_val.create_dataset(
                    "0", (timesteps, len(values), len(values[0])),
                    dtype=numpy.float64, maxshape=(None, len(values),
                                                   len(values[0])))
                v = prop_val["0"]
                prop["space discretization"] = h5py.SoftLink(
                    "/phenomena/{0}/property_sets/{1}/properties/space discretization".format(_name_phenomenon, _name_property_set))
            else:
                prop.create_dataset(
                    "value", (timesteps, len(values)), dtype=numpy.int64,
                    maxshape=(None, len(values)))
                v = prop["value"]

            # Initialise all 'previous' timesteps
            for ts in xrange(0, timesteps):
                v[ts, ...] = values

            prop["time discretization"] = h5py.SoftLink(
                "/phenomena/{0}/property_sets/{1}/properties/time discretization".format(_name_phenomenon, _name_property_set))

        except Exception as e:
            raise ValueError("{} ({})".format(e, name))

    def _property_exists(self, _name_phenomenon, _name_property_set,
                         _name_property):

        self._property_set_exists(_name_phenomenon, _name_property_set)

        if _name_property in self.list_property_sets_prop(_name_phenomenon,
                                                          _name_property_set):
            return
        else:
            msg = "Could not find property '{0}' in property set '{2}' of \
            phenomenon '{1}'".format(
                _name_property, _name_phenomenon, _name_property_set)
            raise ValueError(msg)
