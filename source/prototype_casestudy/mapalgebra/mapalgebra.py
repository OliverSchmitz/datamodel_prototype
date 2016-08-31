'''
@author: Merijn de Bakker, Utrecht University 2016

mapalgebra.py contains model operations.

'''
from datamodel import phenomenon, pset, prop, domain, val, create_return_prop
from utils import datatypes
import python_hdf5
import utils
import copy
import numpy as np


# read the data from HDF5 and construct a phenomenon.
def read(filelocation):

    phen = phenomenon()
    hdf5file = python_hdf5.lue_h5py(filelocation)

    #retrieve phenomenon name from dataset
    phen_list = hdf5file.list_phenomena()
    phen_name = phen_list[0]
    phen.name = phen_name

    # retrieve and set data for property sets
    pset_list = hdf5file.list_property_sets(phen_name)

    for ps_name in pset_list:

        ps = pset()
        ps.name = ps_name

        #retrieve properties for property set
        p_list = hdf5file.list_property_sets_prop(phen_name, ps_name)
        dom = domain()
        dom = utils.create_domain(dom, hdf5file, phen_name, ps_name,
                   p_list[0])
        dom.pset = ps

        setattr(phen, ps_name, ps)

        setattr(ps, 'domain', dom)

        for p_name in p_list:

            if "discretization" in p_name:
                continue

            p = prop()
            p.name = p_name

            #set the data type in the property. For now, agent or field
            if utils.is_field(hdf5file, phen_name, ps_name):
                p.datatype = datatypes.field
            else:
                p.datatype = datatypes.agent

            v = val()
            v = utils.create_value(v, hdf5file, phen_name, ps_name, p_name)
            v.prop = p

            # get the discretization of a field property
            if p.datatype == datatypes.field:
                p.space_discretization = [hdf5file.nr_cols(phen_name, ps_name,
                           p_name), hdf5file.nr_rows(phen_name, ps_name,
                           p_name)]
            else:
                p.space_discretization = None

            p.time_discretization = None
            setattr(ps, p_name, p)

            # set the domain for this property
            setattr(p, 'domain', dom)

            # set v for this property
            setattr(p, 'value', v)

    hdf5file.close_current_hdf5_file()

    return phen


# write the current data in the phenomenon to HDF5
def write(phen, filelocation, t):
    hdf5file = python_hdf5.lue_h5py(filelocation)

    psets = get_all_psets_in_phen(phen)

    # set current value, add new properties if created during this timestep
    for pset in psets:

        props = get_all_properties_in_pset(pset)
        prop_names = [p.name for p in props]
        p_list = hdf5file.list_property_sets_prop(phen.name, pset.name)

        new_props = set(prop_names) - set(p_list)

        for prop_name in p_list:
            prop = get_property_in_phen(phen, prop_name)
            value_arr = create_numpyarray_from_dict(
                        prop.value.get_current_values())
            hdf5file.set_property_value(phen.name, pset.name, prop.name,
                        value_arr)

        for prop_name in new_props:
            prop = get_property_in_phen(phen, prop_name)
            value_arr = create_numpyarray_from_dict(
                        prop.value.get_current_values())
            hdf5file.add_property(phen.name, pset.name, prop.name, value_arr)
            hdf5file.set_property_value(phen.name, pset.name, prop.name,
                        value_arr)

    # set new locations
    for pset in psets:

        if props[0].datatype == utils.datatypes.agent:
            d = pset.domain.get_current_domains()
            loc_list = create_locationlist_from_dict(d)
            hdf5file.set_locations(phen.name, pset.name, props[0].name,
                       loc_list)

    if hdf5file.current_timestep(phen.name, psets[0].name) != t + 1:
        hdf5file.update_time_domain(phen.name, psets[0].name, t)

    hdf5file.close_current_hdf5_file()


# return the max val of arg1 and arg2 (for the time being) an agent or field,
# and a scalar data type
def maximum(arg2, arg1):
    self_current_value = copy.deepcopy(arg1.value.get_current_values())
    arg2_as_array = np.array([arg2])

    if not(isinstance(arg2, datatypes.scalar_types)) or (
                 arg1.datatype != datatypes.agent) and (
                 arg1.datatype != datatypes.field):

        print 'maximum: wrong arguments. first argument should be scalar, \
                second argument agent or field'
        return None

    if arg1.datatype == datatypes.agent and isinstance(arg2,
    datatypes.scalar_types):
        for item in self_current_value:
            if self_current_value[item] > arg2:
                continue
            else:
                self_current_value[item] = arg2_as_array
    elif arg1.datatype == datatypes.field and isinstance(arg2,
    datatypes.scalar_types):
        for item in self_current_value:
            self_current_value[item] = np.maximum(self_current_value[item],
                      arg2_as_array)

    return create_return_prop(arg1, self_current_value)


# return the min val of arg1 and arg2 (for the time being) an agent or field,
# and a scalar data type
def minimum(arg2, arg1):
    self_current_value = copy.deepcopy(arg1.value.get_current_values())
    arg2_as_array = np.array([arg2])

    if not(isinstance(arg2, datatypes.scalar_types)) or (
                 arg1.datatype != datatypes.agent) and (
                 arg1.datatype != datatypes.field):

        print 'minimum: wrong arguments. first argument should be scalar, \
                second argument agent or field'
        return None

    if arg1.datatype == datatypes.agent and isinstance(arg2,
    datatypes.scalar_types):
        for item in self_current_value:
            if self_current_value[item] <= arg2:
                continue
            else:
                self_current_value[item] = arg2_as_array
    elif arg1.datatype == datatypes.field and isinstance(arg2,
    datatypes.scalar_types):
        for item in self_current_value:
            self_current_value[item] = np.minimum(self_current_value[item],
                      arg2_as_array)

    return create_return_prop(arg1, self_current_value)


# window operation. Currently, sum, or count for a window of four is
# implemented
def window(field_arg, aggregation, n):
    self_current_value = copy.deepcopy(field_arg.value.get_current_values())
    self_new_value = copy.deepcopy(field_arg.value.get_current_values())

    # message for not supported options
    if not((aggregation == 'sum' or aggregation == 'count') and
           n == 'manhattan'):
        print 'chosen aggregation method (', aggregation, ') and/or size not \
                implemented'
        return None

    for item in self_current_value:
        dims = self_current_value[item].shape

        for row in range(0, dims[0]):
            for col in range(0, dims[1]):
                if aggregation == 'sum':
                    if col - 1 < 0:
                        cell_left = 0
                    else:
                        cell_left = self_current_value[item][row, col - 1]

                    if col + 1 > dims[1] - 1:
                        cell_right = 0
                    else:
                        cell_right = self_current_value[item][row, col + 1]

                    if row - 1 < 0:
                        cell_up = 0
                    else:
                        cell_up = self_current_value[item][row - 1, col]

                    if row + 1 > dims[0] - 1:
                        cell_down = 0
                    else:
                        cell_down = self_current_value[item][row + 1, col]

                elif aggregation == 'count':
                    if col - 1 < 0:
                        cell_left = 0
                    else:
                        cell_left = 1

                    if col + 1 > dims[1] - 1:
                        cell_right = 0
                    else:
                        cell_right = 1

                    if row - 1 < 0:
                        cell_up = 0
                    else:
                        cell_up = 1

                    if row + 1 > dims[0] - 1:
                        cell_down = 0
                    else:
                        cell_down = 1

                self_new_value[item][row, col] = cell_left + cell_right \
                        + cell_up + cell_down

    return create_return_prop(field_arg, self_new_value)


# movement of agents. returns new domain object with new locations
def gaussian_move(agent_arg, field_arg, sigma):

    self_current_domain = copy.deepcopy(agent_arg.domain.get_current_domains())
    boolean_field = field_arg.value.get_current_value_for_id(0)

    if not np.dtype(boolean_field[0, 0]) == np.bool:
        print 'second argument is not a boolean field'
        return None

    if get_all_properties_in_pset(agent_arg)[0].datatype == datatypes.agent:
        for item in self_current_domain:
            current_x = self_current_domain[item][0]
            current_y = self_current_domain[item][1]

            new_loc = utils.get_new_random_loc(current_x, current_y, sigma)

            try:
                utils.get_cell_at_loc(
                       field_arg.domain.get_current_domain_for_id(0),
                       field_arg.space_discretization, new_loc)
            except:
                new_loc = [current_x, current_y]

            while not utils.get_cell_value_at_location(
                    boolean_field,
                    field_arg.domain.get_current_domain_for_id(0),
                    field_arg.space_discretization, new_loc)[2]:

                new_loc = utils.get_new_random_loc(current_x, current_y, sigma)

                try:
                    utils.get_cell_at_loc(
                       field_arg.domain.get_current_domain_for_id(0),
                       field_arg.space_discretization, new_loc)
                except:
                    new_loc = [current_x, current_y]

            self_current_domain[item] = np.array(new_loc)
    else:
        print 'move: operation not supported for data type'
        return None

    d = domain()
    d.set_as_current_domains(self_current_domain)
    agent_arg.domain = d

    # update the domain reference in the properties.
    # this code should be moved elsewhere in the future.
    for v in agent_arg.__dict__.itervalues():
        if type(v) == prop:
            v.domain = d

    return d


def get_all_psets_in_phen(phen):

    pset_list = []

    for value in phen.__dict__.itervalues():
        if isinstance(value, pset):
            pset_list.append(value)

    if len(pset_list) > 0:
        return pset_list
    else:
        print "get_all_psets_in_phen: no property sets found "
        return None


def get_all_properties_in_pset(pset):

    p_list = []

    for value in pset.__dict__.itervalues():
        if isinstance(value, prop):
            p_list.append(value)

    if len(p_list) > 0:
        return p_list
    else:
        print "get_all_properties_in_pset: no properties found "
        return None


def get_property_in_phen(phen, p_name):

    psets = get_all_psets_in_phen(phen)

    for pset in psets:
        props = get_all_properties_in_pset(pset)

        for prop in props:
            if prop.name == p_name:
                return prop
    print "get_property_in_phen: property not found"
    return None


def create_numpyarray_from_dict(numpy_dict):
    return_array = []

    arr_shape = numpy_dict[0].shape

    #agent
    if arr_shape[0] == 1:
        for key in numpy_dict:
            return_array.append(numpy_dict[key].tolist()[0])
    #field
    else:
        for key in numpy_dict:
            return_array = (numpy_dict[key].tolist())

    return return_array


def create_locationlist_from_dict(location_dict):
    loc_list = []

    for value in location_dict.itervalues():
        loc_tuple = tuple(value)
        loc_list.append(loc_tuple)

    return loc_list


def create_image(field_prop, agent_pset, t):
    utils.make_png(field_prop.value.get_current_value_for_id(0),
            create_locationlist_from_dict(
            agent_pset.domain.get_current_domains()), t)
