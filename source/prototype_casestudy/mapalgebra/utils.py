'''
@author: Merijn de Bakker, Utrecht University 2016

Module helper contains helper functions used in the mapalgebra module.
'''
import numpy as np
import math
import types
import matplotlib.pyplot as plt
import os
import random


def create_domain(dom, f, phen_name, pset_name, p_name):

    #get a list with item ids
    item_ids = f.item_ids(phen_name, pset_name)

    #check whether the property is a field
    ps_is_field = is_field(f, phen_name, pset_name)

    #iterator counter
    counter = 0

    if ps_is_field:
        spatial_extent = np.asarray(f.get_spatial_extent_pset(phen_name,
                  pset_name))

        for i in item_ids:
            dom.set_as_current_domain_for_id(i, spatial_extent)
            counter += 1

    else:
        locations = f.get_locations(phen_name, pset_name, p_name)

        for i in item_ids:
            [locations[counter][0], locations[counter][1]]
            dom.set_as_current_domain_for_id(i, np.asarray(
                       [locations[counter][0], locations[counter][1]]))
            counter += 1

    return dom


def create_value(v, f, phen_name, pset_name, p_name):

    # get a list with item ids
    item_ids = f.item_ids(phen_name, pset_name)

    # iterator counter
    counter = 0

    retrieved_data = f.get_property_value(phen_name, pset_name, p_name).astype(
               float)

    if is_field(f, phen_name, pset_name):
        for i in item_ids:
            v.set_as_current_value_for_id(i, retrieved_data)
            counter += 1
    else:
        for i in item_ids:
            v.set_as_current_value_for_id(i, np.asarray(
                        [retrieved_data[counter]]))
            counter += 1

    return v


def get_datatype(val):
    if val.get_current_value_for_id(0).ndim >= 2:
        return datatypes.field
    else:
        return datatypes.agent


def is_field(f, phen_name, pset_name):

    p_list = f.list_property_sets_prop(phen_name, pset_name)

    return f.is_field(phen_name, pset_name, p_list[0])


def get_cell_at_loc(cells_domain, cells_discretization, location):
    x_min, y_min, x_max, y_max = cells_domain
    x_coord = location[0]
    y_coord = location[1]
    west = x_min
    north = y_max
    cell_size = get_cellsize(x_max, x_min, cells_discretization[0])

    x_col = (x_coord - west) / cell_size
    y_row = (north - y_coord) / cell_size

    row_idx = int(math.floor(y_row))
    col_idx = int(math.floor(x_col))

    nr_rows = int(math.floor((y_max - y_min) / cell_size))
    nr_cols = int(math.floor((x_max - x_min) / cell_size))

    if (col_idx + 1) > nr_cols or (col_idx) <= 0:
        msg = "Column index ({0}) out of range (from 1 to {1}))".format(
                    col_idx + 1, nr_cols)
        raise ValueError(msg)

    if (row_idx + 1) > nr_rows or (row_idx) <= 0:
        msg = "Row index ({0}) out of range (from 1 to {1})".format(
                    row_idx + 1, nr_rows)
        raise ValueError(msg)

    return row_idx, col_idx


def get_cell_value_at_location(cells, cells_domain, cells_discretization,
                               location):

    row_idx, col_idx = get_cell_at_loc(cells_domain, cells_discretization,
                                       location)

    return [row_idx, col_idx, cells[row_idx, col_idx]]


def get_new_random_loc(current_x, current_y, sigma):
    return [random.normalvariate(current_x, sigma),
                    random.normalvariate(current_y, sigma)]


# assumes square cells
def get_cellsize(x_max, x_min, nr_cols):

    return (x_max - x_min) / nr_cols


def create3Darray(data):
    if data.ndim == 1:
        data = np.expand_dims(data, 2)

    return np.expand_dims(data, 3)


class datatypes:
    scalar_types = (types.IntType, types.LongType, types.FloatType,
                    types.ListType, np.ndarray)
    field, agent = range(2)

    @staticmethod
    def get_type_string(phenomenon):
        if phenomenon == datatypes.field:
            return 'Raster'
        if phenomenon == datatypes.agent:
            return 'Agent'
        else:
            return ''


def transform(values):
    nr_rows = 100  # 6
    nr_cols = 100  # 4
    cellsize = 25
    """ Transforms x,y PCRaster coordindates to plot canvas coordinates """
    xfac = nr_cols / float(nr_cols * cellsize)
    yfac = nr_rows / float(nr_rows * cellsize)

    x = values[0] * xfac - 0.5
    y = -1.0 * values[1] * yfac - 0.5

    return x, y


def make_png(field, agents, timestep):
    plt.rcParams.update({'font.size': 22})
    plt.figure(figsize=(8, 8), dpi=80)
    plt.imshow(field, interpolation="none",
               extent=[0, 100, 100, 0], origin='upper',
               cmap=plt.get_cmap("Greens"), label='biomass')
    plt.title("timestep {0}".format(timestep))

    plt.colorbar(shrink=0.7)

    locs = []
    for a in agents:
        locs.append(transform(a))
    x, y = zip(*locs)

    plt.plot(x, y, 'ro', color='red', markersize=4, label='cows')
    plt.ylim(len(field), 0)

    # min/max biomass values...
    plt.clim(0, 20)

    plt.xticks([])
    plt.yticks([])

    plt.legend(loc='upper right')

    plt.savefig(os.path.join("../data/model_t{:05d}.png".format(timestep)),
                transparent=False, bbox_inches='tight')
    plt.close()
