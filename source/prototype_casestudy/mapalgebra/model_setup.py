# Helper script that
# - generates LUE datasets for biomass and cows
# - removes previous image files
import os
import glob
import random
import numpy
import pickle
import h5py


def _add_agent_property(a_prop, _name_phenomenon, _name_property_set, name,
            values, nr_cows):
    prop = a_prop.create_group(name)
    prop.create_dataset(
        "value", (1, nr_cows), dtype=numpy.int64, maxshape=(None, nr_cows))

    v = prop["value"]
    v[...] = values

    prop["time discretization"] = h5py.SoftLink(
        "/phenomena/{0}/property_sets/{1}/properties/time discretization".
        format(_name_phenomenon, _name_property_set))


def _add_field_property(a_prop, _name_phenomenon, _name_property_set, name,
            values):
    rows = 100
    cols = 100
    prop = a_prop.create_group(name)
    prop_val = prop.create_group("value")

    prop_val.create_dataset(
        "0", (1, rows, cols), dtype=numpy.float64, maxshape=(None, rows, cols))

    v = prop_val["0"]
    v[...] = values

    prop["time discretization"] = h5py.SoftLink(
        "/phenomena/{0}/property_sets/{1}/properties/time discretization".
        format(_name_phenomenon, _name_property_set))

    prop["space discretization"] = h5py.SoftLink(
        "/phenomena/{0}/property_sets/{1}/properties/space discretization".
        format(_name_phenomenon, _name_property_set))


def _generate_cows(data_path):
    # settings according to the biomass field
    # initial cow attributes
    init_x = 1250
    init_y = -1750
    nr_cows = 50
    init_weight = 600

    name_phenomenon = "cows"
    name_property_set = "location"
    name_property = "weight"

    # spreading locations and weight
    sigma_locs = 5
    sigma_weight = 25

    f = h5py.File(os.path.join(data_path, "cows.hdf5"), "w")

    # plain generation of cows LUE
    cow_locs = []

    for c in range(0, nr_cows):
        cow_locs.append(
            (random.normalvariate(init_x, sigma_locs),
             random.normalvariate(init_y, sigma_locs)))

    phenomena = f.create_group("phenomena")
    flock = phenomena.create_group(name_phenomenon)
    prop_set = flock.create_group("property_sets")
    cows = prop_set.create_group(name_property_set)

    domain = cows.create_group("domain")
    domain["item"] = xrange(0, nr_cows)

    domain_time = domain.create_group("time")

    # make compound
    time_start = numpy.dtype([("year", numpy.int64), ("month", numpy.int64)])
    time_dur = numpy.dtype([("count", numpy.int64)])
    time_extent2 = numpy.dtype([("start", time_start), ("duration", time_dur)])

    domain_time.create_dataset("item", (1,), dtype=time_extent2)

    val = domain_time["item"]
    val[...] = (1980, 1), (1,)

    domain_space = domain.create_group("space")
    domain_space["time discretization"] = h5py.SoftLink(
        "/phenomena/flock/property_sets/cows/properties/time discretization")

    locs = numpy.dtype([("d0", numpy.float64), ("d1", numpy.float64)])
    domain_space.create_dataset(
        "item", (1, nr_cows), dtype=locs, maxshape=(None, nr_cows))

    val = domain_space["item"]
    val[...] = cow_locs

    properties = cows.create_group("properties")
    properties_time_discr = properties.create_group("time discretization")

    timesteps = nr_cows * [(1,)]

    properties_time_discr["value"] = timesteps

    cow_weights = []

    for c in range(0, nr_cows):
        cow_weights.append(
            init_weight + random.randint(-1.0 * sigma_weight, sigma_weight))

    _add_agent_property(properties, name_phenomenon,
                        name_property_set, name_property, cow_weights, nr_cows)


def _generate_biomass(data_path):
    rows = 100
    cols = 100
    north = 0.0
    west = 0.0
    length = 25
    name_phenomenon = "grass"
    name_property_set = "area"
    name_property = "biomass"

    f = h5py.File(os.path.join(data_path, "grass.hdf5"), "w")

    # plain generation of biomass LUE
    phenomena = f.create_group("phenomena")
    flock = phenomena.create_group(name_phenomenon)
    prop_set = flock.create_group("property_sets")
    cows = prop_set.create_group(name_property_set)

    domain = cows.create_group("domain")
    domain["item"] = (0,)

    domain_space = domain.create_group("space")
    # make compound
    minimum = numpy.dtype([("d0", numpy.float64), ("d1", numpy.float64)])
    maximum = numpy.dtype([("d0", numpy.float64), ("d1", numpy.float64)])

    space_extent = numpy.dtype([("min", minimum), ("max", maximum)])

    domain_space.create_dataset("item", (1,), dtype=space_extent)

    val = domain_space["item"]
    val[...] = (west, north - rows * length), (west + cols * length, north)

    domain_time = domain.create_group("time")

    # make compound
    time_start = numpy.dtype([("year", numpy.int64), ("month", numpy.int64)])
    time_dur = numpy.dtype([("count", numpy.int64)])
    time_extent2 = numpy.dtype([("start", time_start), ("duration", time_dur)])

    domain_time.create_dataset("item", (1,), dtype=time_extent2)

    val = domain_time["item"]
    val[...] = (1980, 1), (1,)

    properties = cows.create_group("properties")

    properties_space_discr = properties.create_group("space discretization")
    space = [(rows, cols)]
    properties_space_discr["value"] = space

    properties_time_discr = properties.create_group("time discretization")

    timesteps = [(1,)]

    properties_time_discr["value"] = timesteps

    with open(os.path.join(data_path, "initial_biomass.pkl"), "r") as f:
        val = pickle.load(f)

    _add_field_property(
        properties, name_phenomenon, name_property_set, name_property, val)


def _remove_images(model_path):
    """ Removes output images files from previous run """

    old_files = glob.glob(os.path.join(model_path, "model_*.png"))

    for f in old_files:
        os.remove(f)


def initialize(seed=0):
    """ Removes old files and initialises new datasets """
    data_path = os.path.join("..", "data")  # os.path.join("../", "data")
    model_path = os.path.join("..", "model")  # os.path.join("../", "model")

    random.seed(seed)

    _generate_cows(data_path)
    _generate_biomass(data_path)
    _remove_images(data_path)
    _remove_images(model_path)

if __name__ == "__main__":
    initialize(1)
