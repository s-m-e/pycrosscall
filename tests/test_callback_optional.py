# -*- coding: utf-8 -*-

"""

ZUGBRUECKE
Calling routines in Windows DLLs from Python scripts running on unixlike systems
https://github.com/pleiszenburg/zugbruecke

	tests/test_callback_optional.py: Optional callback routines as arguments

	Required to run on platform / side: [UNIX, WINE]

	Copyright (C) 2017-2020 Sebastian M. Ernst <ernst@pleiszenburg.de>

<LICENSE_BLOCK>
The contents of this file are subject to the GNU Lesser General Public License
Version 2.1 ("LGPL" or "License"). You may not use this file except in
compliance with the License. You may obtain a copy of the License at
https://www.gnu.org/licenses/old-licenses/lgpl-2.1.txt
https://github.com/pleiszenburg/zugbruecke/blob/master/LICENSE

Software distributed under the License is distributed on an "AS IS" basis,
WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License for the
specific language governing rights and limitations under the License.
</LICENSE_BLOCK>

"""

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# C
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

HEADER = """
typedef int16_t {{ SUFFIX }} (*conveyor_belt)(int16_t index);

{{ PREFIX }} int16_t {{ SUFFIX }} use_optional_callback_a(
	int16_t in_data,
	conveyor_belt process_data
	);

{{ PREFIX }} int16_t {{ SUFFIX }} use_optional_callback_b(
	int16_t in_data,
	conveyor_belt process_data
	);
"""

SOURCE = """
{{ PREFIX }} int16_t {{ SUFFIX }} use_optional_callback_a(
	int16_t in_data,
	conveyor_belt process_data
	)
{
	int16_t tmp;
	if(process_data) {
		tmp = process_data(in_data);
	} else {
		tmp = in_data;
	}
	return tmp * 2;
}

{{ PREFIX }} int16_t {{ SUFFIX }} use_optional_callback_b(
	int16_t in_data,
	conveyor_belt process_data
	)
{
	int16_t tmp;
	if(process_data) {
		tmp = process_data(in_data);
	} else {
		tmp = in_data;
	}
	return tmp * 2;
}
"""

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# IMPORT
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

from .lib.ctypes import get_context

import pytest

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASSES AND ROUTINES
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class sample_class_a:
    def __init__(self, conv, ctypes, dll_handle):

        if conv == "cdll":
            func_type = ctypes.CFUNCTYPE
        elif conv == "windll":
            func_type = ctypes.WINFUNCTYPE
        else:
            raise ValueError("unknown calling convention", conv)
        conveyor_belt = func_type(ctypes.c_int16, ctypes.c_int16)

        self._use_optional_callback = dll_handle.use_optional_callback_a
        self._use_optional_callback.argtypes = (ctypes.c_int16, conveyor_belt)
        self._use_optional_callback.restype = ctypes.c_int16

        @conveyor_belt
        def process_data(in_data):
            return in_data ** 2

        self.__process_data__ = process_data

    def use_optional_callback(self, some_data):
        return self._use_optional_callback(some_data, self.__process_data__)


class sample_class_b:
    def __init__(self, ctypes, dll_handle):
        self._use_optional_callback = dll_handle.use_optional_callback_b
        self._use_optional_callback.argtypes = (ctypes.c_int16, ctypes.c_void_p)
        self._use_optional_callback.restype = ctypes.c_int16

    def do_not_use_optional_callback(self, some_data):
        return self._use_optional_callback(some_data, None)


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# TEST(s)
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@pytest.mark.parametrize("arch,conv,ctypes,dll_handle", get_context(__file__))
def test_use_optional_callback(arch, conv, ctypes, dll_handle):
    sample = sample_class_a(conv, ctypes, dll_handle)
    assert 18 == sample.use_optional_callback(3)


@pytest.mark.parametrize("arch,conv,ctypes,dll_handle", get_context(__file__))
def test_do_not_use_optional_callback(arch, conv, ctypes, dll_handle):
    sample = sample_class_b(ctypes, dll_handle)
    assert 14 == sample.do_not_use_optional_callback(7)
