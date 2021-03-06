from textx import get_model, get_children_of_type
from functools import reduce


def check_scalar_ref(scalar_ref):
    def myassert(ref):
        if not ref.default_value:
            raise Exception("{}: {}.{} needs to have a default value".format(
                get_model(ref)._tx_filename,
                ref.parent.name,
                ref.name))

    if scalar_ref.ref2:
        myassert(scalar_ref.ref2)
    elif scalar_ref.ref1:
        myassert(scalar_ref.ref1)
    else:
        myassert(scalar_ref.ref0)


def check_array_dimensions(array_dimension):
    if len(array_dimension.parent.array_dimensions) > 1:
        if not array_dimension.array_index_name:
            raise Exception("{}: array {} needs to have named dimensions: specify [SIZE:NAME]".format(
                get_model(array_dimension)._tx_filename, array_dimension.parent.name))


def check_array_attribute(array_attribute):
    """
    check if array size depends only on attributes defined before it in the struct
    :param array_attribute:
    :return: None
    throws on error
    """
    from itemlang.itemc.metamodel_formula import ScalarRef
    dependencies = map(lambda x: x.ref0,
                       reduce(lambda l1, l2: l1 + l2,
                              map(lambda node: get_children_of_type(ScalarRef, node), array_attribute.array_dimensions),
                              []
                              )
                       )
    struct = array_attribute.parent
    index_of_array = struct.attributes.index(array_attribute)
    available_infos_until_this_array = struct.attributes[0:index_of_array]
    for d in dependencies:
        if not (d in available_infos_until_this_array):
            raise Exception(
                "array {}.{} depends on {}.{} not defined before it in {}.".format(
                    struct.name, array_attribute.name,
                    struct.name, d.name,
                    get_model(struct)._tx_filename))


class CheckRawTypes(object):
    def __init__(self, options):
        if options:
            self.options = options
        else:
            self.options = {}

    def __call__(self, struct):
        from itemlang.itemc.metamodel import RawType

        def check_raw_type_is_defined_for_language(rawtype):
            if "generate_cpp" in self.options.keys() and self.options["generate_cpp"]:
                if rawtype.genericType == "custom" and not rawtype.cpptype:
                    raise Exception("C++ type is required to generate C++ code for {} in {}".format(
                        rawtype.name,
                        get_model(rawtype)._tx_filename))
            if "generate_python" in self.options.keys() and self.options["generate_python"]:
                if rawtype.genericType == "custom" and not rawtype.pythontype:
                    raise Exception("python type is required to generate python code for {} in {}".format(
                        rawtype.name,
                        get_model(rawtype)._tx_filename))
            if "generate_python_construct" in self.options.keys() and self.options["generate_python_construct"]:
                if not rawtype.pythonconstructtype:
                    raise Exception(
                        "python-construct type is required to generate python code for {} in {}".format(
                            rawtype.name,
                            get_model(rawtype)._tx_filename))

        for t in set(filter(lambda x: isinstance(x, RawType), map(lambda x: x.type, struct.attributes))):
            check_raw_type_is_defined_for_language(t)


def check_raw_type_has_defined_bits(rawtype):
    if rawtype.genericType != "custom" and not rawtype.genericBits:
        raise Exception("Bits need to be specified for {} in {}".format(
            rawtype.name,
            get_model(rawtype)._tx_filename))
