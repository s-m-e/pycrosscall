# -*- coding: utf-8 -*-

"""

ZUGBRUECKE
Calling routines in Windows DLLs from Python scripts running on unixlike systems
https://github.com/pleiszenburg/zugbruecke

    src/zugbruecke/core/callback_client.py: Classes for managing callback routines

    Required to run on platform / side: [UNIX, WINE]

    Copyright (C) 2017-2021 Sebastian M. Ernst <ernst@pleiszenburg.de>

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
# IMPORT
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import traceback
from typing import Callable, Dict, List

from .abc import CallbackClientABC, DataABC, LogABC, RpcServerABC
from .typeguard import typechecked


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CALLBACK CLIENT CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@typechecked
class CallbackClient(CallbackClientABC):
    """
    Representing a callback function
    """

    def __init__(
        self,
        name: str,
        handler: Callable,
        rpc_server: RpcServerABC,
        data: DataABC,
        log: LogABC,
        argtypes_d: List,
        restype_d: Dict,
        memsync_d: List,
    ):

        self._name = name
        self._handler = handler
        self._data = data
        self._log = log
        self._argtypes_d = argtypes_d
        self._restype_d = restype_d
        self._memsync_d = memsync_d

        rpc_server.register_function(self, public_name=name)

    def __call__(self, arg_message_list, arg_memory_list):

        # Log status
        self._log.out(
            '[callback-client] Trying to call callback routine "%s" ...' % self._name
        )

        try:

            # Unpack arguments
            args_list = self._data.arg_list_unpack(arg_message_list, self._argtypes_d)

            # Unpack pointer data
            self._data.server_unpack_memory_list(
                args_list, arg_memory_list, self._memsync_d
            )

            # Default return value
            return_value = None

        except Exception as e:

            # Log status
            self._log.out("[callback-client] ... call preparation failed!")

            # Push traceback to log
            self._log.err(traceback.format_exc())

            raise e

        # This is risky
        try:

            # Call actual callback function (ctypes function pointer)
            return_value = self._handler(*tuple(args_list))

        except Exception as e:

            # Log status
            self._log.out("[callback-client] ... call failed!")

            # Push traceback to log
            self._log.err(traceback.format_exc())

            # Pack return package and return it
            return {
                "args": arg_message_list,
                "return_value": return_value,
                "memory": arg_memory_list,
                "success": False,
                "exception": e,
            }

        try:

            # Pack memory for return
            self._data.server_pack_memory_list(
                args_list, return_value, arg_memory_list, self._memsync_d
            )

            # Get new arg message list
            arg_message_list = self._data.arg_list_pack(args_list, self._argtypes_d)

            # Pack return value
            return_message = self._data.return_msg_pack(return_value, self._restype_d)

            # Log status
            self._log.out("[callback-client] ... done.")

            # Ship data back to Wine side
            return {
                "args": arg_message_list,
                "return_value": return_message,
                "memory": arg_memory_list,
                "success": True,
                "exception": None,
            }

        except Exception as e:

            # Log status
            self._log.out("[callback-client] ... call post-processing failed!")

            # Push traceback to log
            self._log.err(traceback.format_exc())

            raise e
