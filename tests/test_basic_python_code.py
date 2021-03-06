from __future__ import absolute_import
from __future__ import unicode_literals
from os.path import dirname, exists
from shutil import rmtree
import os.path
from pytest import raises
import importlib
import numpy as np


def test_basic_python_code():
    import itemlang.itemc.codegen as codegen

    #################################
    # Model definition and Code creation
    #################################

    this_folder = dirname(__file__)
    # cleanup old generated code
    if exists(os.path.join(this_folder, "mypackage1")):
        rmtree(os.path.join(this_folder, "attributes"))
        rmtree(os.path.join(this_folder, "mypackage1"))
    # check that no old generated code is present
    assert not exists(os.path.join(this_folder, "mypackage1/test/Header.py"))
    assert not exists(os.path.join(this_folder, "mypackage1/test/Data.py"))
    assert not exists(os.path.join(this_folder, "mypackage1/test/Simple.py"))

    codegen.codegen(srcgen_folder=this_folder,
                    generate_python=True,
                    model_string=
                    """
                    // model
                    package types {
                    type int   as custom {   python: "int" with format "i" }
                    type float as custom {   python: "float" with format "f" }
                    type UINT8 as custom {   python: "uint8"  from 'numpy' with format "B" }
                    type UINT16 as custom {   python: "uint16" from 'numpy' with format "H" }
                    }
                    package mypackage1 {
                    target_namespace "mypackage1.test"
                    struct Header {
                        scalar proofword : types.int
                        scalar N : types.int { default = "0x16" }
                        scalar k : types.int
                        array info : types.float[10]
                    }
                    struct Data {
                        scalar header   : Header
                        scalar n        : types.int {default="5"}
                        scalar x_f      : types.float
                        scalar x_i      : types.int
                        scalar x_ui16   : types.UINT16
                        array  a_ui16   : types.UINT16
                                            [header.N:master_index]
                                            [n:client_index]
                                            [2:real_imag]
                        array  a_f      : types.float
                                            [header.N:master_index]
                                            [n:client_index]
                        array  headers  : Header
                                            [header.N:master_index]
                                            [n:client_index]
                    }
                    struct Simple {
                        scalar n        : types.UINT16 {default="5"}
                        scalar x        : types.UINT16
                        array  a_ui16   : types.UINT16[n]
                    }
                    }
                    """)

    #################################
    # Using the model classes
    #################################

    # have the classes been created?
    assert exists(os.path.join(this_folder, "mypackage1/test/Header.py"))
    assert exists(os.path.join(this_folder, "mypackage1/test/Data.py"))
    assert exists(os.path.join(this_folder, "mypackage1/test/Simple.py"))

    # use them:
    header_lib = importlib.import_module("mypackage1.test.Header")
    data_lib = importlib.import_module("mypackage1.test.Data")
    simple_lib = importlib.import_module("mypackage1.test.Simple")
    tool_lib = importlib.import_module("attributes.tools")

    header = header_lib.Header()
    data = data_lib.Data()

    # allowed access
    header.N = 11

    # disallowd acces (size controlling attribute)
    with raises(Exception, match=r'.*illegal access.*read only.*'):
        data.header.N = 12

    # set size (multiple times)
    data.init(header, 33)
    assert data.a_ui16.shape == (11, 33, 2)
    header.N = 13
    data.init(header, 33)
    # check also linked sizes (more than one array with correlated sizes)
    assert data.a_ui16.shape == (13, 33, 2)
    assert data.a_f.shape == (13, 33)
    assert data.headers.shape == (13, 33)

    simple = simple_lib.Simple()
    simple.init(3)
    assert simple.a_ui16.shape == (3,)
    simple.a_ui16 = np.linspace(0, 90, 3, dtype=np.uint16)

    simple_as_text = tool_lib.pprint(simple)
    assert simple_as_text == """Simple {
  n = 3
  x = 0
  a_ui16[] = [ 0 45 90 ]
}
"""
    # I/O
    with open('data.bin', 'wb') as f:
        tool_lib.bin_write(simple, f)

    simple2 = simple_lib.Simple()
    with open('data.bin', 'rb') as f:
        tool_lib.bin_read(simple2, f)

    assert simple.n == simple2.n
    assert simple.x == simple2.x
    assert len(simple.a_ui16) == len(simple2.a_ui16)
    for k in range(len(simple.a_ui16)):
        assert simple.a_ui16[k] == simple2.a_ui16[k]

    #################################
    # END
    #################################

    rmtree(os.path.join(this_folder, "mypackage1"))
    rmtree(os.path.join(this_folder, "attributes"))
    assert not exists(os.path.join(this_folder, "mypackage1/test/Header.py"))
    assert not exists(os.path.join(this_folder, "mypackage1/test/Data.py"))
    assert not exists(os.path.join(this_folder, "mypackage1/test/Simple.py"))
    assert not exists(os.path.join(this_folder, "mypackage1"))
    assert not exists(os.path.join(this_folder, "attributes"))
