'''
@author: Merijn de Bakker, Utrecht University 2016

Model datamodel.py contains the data model and arithmetic operators. The data
model is implemented exactly as the conceptual data model, thus with 0..1
associations between the concepts. Extra methods are written to retrieve relate
lower-level concepts to higher level concepts.

Only operators necessary for the current models are implemented.
'''
from utils import datatypes
import numpy as np
import utils
import copy
import operator


# phenomenon implementation
class phenomenon(object):
    file_location = None
    _all = set()

    def __init__(self):
        self.__class__._all.add(self)

    def __getattribute__(self, name):
        entity = object.__getattribute__(self, name)
        try:
            return entity
        except:
            print "property set not found"

    # a phenomenon has zero to n psets
    def __setattr__(self, name, value):
        if isinstance(value, pset):
            self.__dict__[name] = value
        if name == 'name':
            self.__dict__['name'] = value


# property set implementation
class pset(object):

    _all = set()

    def __init__(self):
        self.__class__._all.add(self)

    def __getattribute__(self, name):
        entity = object.__getattribute__(self, name)

        try:
            return entity
        except:
            print "property not found"

    # property set has one domain, and zero to n properties
    def __setattr__(self, name, value):
        if isinstance(value, domain):
            self.__dict__[name] = value
        elif isinstance(value, prop):
            value.name = name
            self.__dict__[name] = value
        elif name == 'name':
            self.__dict__['name'] = value
        else:
            print name, 'could not be set'


# property implementation
class prop(object):

    _all = set()

    def __init__(self):
        self.__class__._all.add(self)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def datatype(self):
        return self._datatype

    @datatype.setter
    def datatype(self, value):
        self._datatype = value

    @property
    def domain(self):
        return self._domain

    @domain.setter
    def domain(self, value):
        self._domain = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    @property
    def space_discretization(self):
        return self._space_discretization

    @space_discretization.setter
    def space_discretization(self, value):
        self._space_discretization = value

    @property
    def time_discretization(self):
        return self._time_discretization

    @time_discretization.setter
    def time_discretization(self, value):
        self._time_discretization = value

    # operators are passed to the apply_operator function to avoid duplication.
    def __add__(self, other):
        # get the new current value
        new_val = apply_operator(operator.add, self, other, flag='n')

        # set the value as the new value
        return create_return_prop(self, new_val)

    # TO BE IMPLEMENTED.
    def __radd__(self, other):
        print 'TO BE IMPLEMENTED'
        pass

    def __sub__(self, other):

        new_val = apply_operator(operator.sub, self, other, flag='n')

        return create_return_prop(self, new_val)

    def __rsub__(self, other):

        new_val = apply_operator(operator.sub, self, other, flag='r')

        return create_return_prop(self, new_val)

    def __mul__(self, other):

        new_val = apply_operator(operator.mul, self, other, flag='n')

        return create_return_prop(self, new_val)

    # TO BE IMPLEMENTED.
    def __rmul__(self, other):

        new_val = apply_operator(operator.mul, self, other, flag='r')

        return create_return_prop(self, new_val)

    def __div__(self, other):

        new_val = apply_operator(operator.div, self, other, flag='n')

        return create_return_prop(self, new_val)

    # TO BE IMPLEMENTED.
    def __rdiv__(self, other):

        new_val = apply_operator(operator.div, self, other, flag='r')

        return create_return_prop(self, new_val)

    def __gt__(self, other):

        other_as_array = np.array([other])

        new_val = apply_operator(operator.gt, self, other_as_array, 'n')

        return create_return_prop(self, new_val)

    # TO BE IMPLEMENTED
    def __lt__(self, other):
        print 'TO BE IMPLEMENTED'
        return None


# domain implementation
class domain(object):

    def __init__(self):
        self.current_domaindict = {}

    def get_current_domain_for_id(self, item_id):
        return self.current_domaindict[item_id]

    def set_as_current_domain_for_id(self, item_id, domain_item):
        self.current_domaindict[item_id] = domain_item

    def get_current_domains(self):
        return self.current_domaindict

    def set_as_current_domains(self, domain_dict):
        self.current_domaindict = domain_dict


# value implementation
class val(object):

    def __init__(self):
        self.datadict = {}

    def get_current_value_for_id(self, item_id):
        return self.datadict[item_id]

    def set_as_current_value_for_id(self, item_id, val_item):
        self.datadict[item_id] = val_item

    def get_current_values(self):
        return self.datadict

    def set_as_current_values(self, value_dict):
        self.datadict = value_dict


# returns the property for a specific value
def get_property_for_value(v):
    for p in prop._all:
        if p.value is v:
            return p
    print 'get_property_for_value: property not found for value '
    return None


# returns the domain for a specific value
def get_domain_for_value(v):
    for p in prop._all:
        if p.value is v:
            return p.domain
    print 'get_domain_for_value: domain not found for value '
    return None


# returns the propertyset for a specific property
def get_propertyset_for_property(p):
    for ps in pset._all:
        if p.name in ps.__dict__:
            return ps
    print ('get_propertyset_for_property: propertyset not found for property ',
            p.name)
    return None


# returns the phenomenon for a specific property
def get_phenomenon_for_property(p):
    for ps in pset._all:
        if p.name in ps.__dict__:
            for phen in phenomenon._all:
                if ps.name in phen.__dict__:
                    return phen
    print ('get_phenomenon_for_property: phenomenon not found for property ',
           p.name)

    return None


# creates a new property instance on the basis of an existing property but with
# a new value.
# operations return a new property which, if necessary replaces an existing
# property.
def create_return_prop(this_p, vals):
    v = val()
    v.set_as_current_values(vals)
    p = prop()
    p.name = ''
    p.datatype = utils.get_datatype(v)
    p.space_discretization = this_p.space_discretization
    p.time_discretization = this_p.time_discretization
    p.value = v
    ps = (this_p)
    p.domain = ps.domain

    return p


# Applies a binary arithmetic or logical operation.
# actual implementation depends on the argument's data types.
def apply_operator(op, arg1, arg2, flag='n'):
    self_current_value = copy.deepcopy(arg1.value.get_current_values())

    # arg1:FIELD,AGENT, arg2:SCALAR
    if flag == 'n' and (
            arg1.datatype == datatypes.field or
            arg1.datatype == datatypes.agent) and isinstance(
            arg2, datatypes.scalar_types):

        for key in self_current_value:
            self_current_value[key] = op(self_current_value[key], arg2)

    # arg1:SCALAR, arg2:FIELD,AGENT
    elif flag == 'r' and (arg1.datatype == datatypes.field or
                          arg1.datatype == datatypes.agent) and (
                          isinstance(arg2, datatypes.scalar_types)):

        for key in self_current_value:
            self_current_value[key] = op(arg2, self_current_value[key])

    # arg1:FIELD, arg2:AGENT
    elif flag == 'n' and arg1.datatype == datatypes.field and (
                  arg2.datatype == datatypes.agent):
        other_current_value = copy.deepcopy(arg2.value.get_current_values())

        for self_key in self_current_value:
            for other_key in other_current_value:
                location = arg2.domain.get_current_domain_for_id(other_key)

                self_domain = arg1.domain.get_current_domain_for_id(self_key)
                [row, col, cell_val] = utils.get_cell_value_at_location(
                    self_current_value[self_key], self_domain,
                    arg1.space_discretization, location)

                self_current_value[self_key][row, col] = op(
                    cell_val, other_current_value[other_key][0])

    # arg1:FIELD, arg2:FIELD
    elif flag == 'n' and arg1.datatype == datatypes.field and (
                  arg2.datatype == datatypes.field):
        other_current_value = copy.deepcopy(arg2.value.get_current_values())
        for key in self_current_value:
            for other_key in other_current_value:
                # simple check to assert that extents do match.
                if np.array_equal(
                        arg1.domain.get_current_domain_for_id(key),
                        arg2.domain.get_current_domain_for_id(other_key)) is (
                                  False):
                    print 'extents do not match'
                else:
                    self_current_value[key] = op(
                        self_current_value[key],
                        other_current_value[other_key])

    # arg1:AGENT, arg2:AGENT
    elif flag == 'n' and arg1.datatype == datatypes.agent and (
                  arg2.datatype == datatypes.agent):
        other_current_value = copy.deepcopy(arg2.value.get_current_values())

        # for now, we allows only agentXagent operations within the same
        # phenomenon, thus having the same number of items
        if len(self_current_value) != len(other_current_value):
            print 'number of items in phenomenon do not match'
        else:
            for key in self_current_value:
                self_current_value[key] = op(
                    self_current_value[key], other_current_value[key])

    # return the altered current value
    return self_current_value
