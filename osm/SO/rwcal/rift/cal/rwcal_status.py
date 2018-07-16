#!/usr/bin/env python
# 
#   Copyright 2016 RIFT.IO Inc
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
#
# @file rwcal_status.py
# @brief This module defines Python utilities for dealing with rwcalstatus codes.

import traceback
import functools
import gi
gi.require_version('RwTypes', '1.0')
gi.require_version('RwCal', '1.0')

from gi.repository import RwTypes, RwCal

def rwcalstatus_from_exc_map(exc_map):
    """ Creates an rwcalstatus decorator from a dictionary mapping exception
    types to rwstatus codes, and return a error object containing Exception details
    """

    # A decorator that maps a Python exception to a particular return code.
    # Also returns an object containing the error msg, traceback and rwstatus
    # Automatically returns RW_SUCCESS when no Python exception was thrown.
    # Prevents us from having to use try: except: handlers around every function call.

    def rwstatus(arg=None, ret_on_failure=None):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwds):
                rwcal_status = RwCal.RwcalStatus()
                try:
                    ret = func(*args, **kwds)

                except Exception as e:
                    rwcal_status.traceback = traceback.format_exc()
                    rwcal_status.error_msg = str(e)

                    ret_code = [status for exc, status in exc_map.items() if isinstance(e, exc)]
                    ret_list = [None] if ret_on_failure is None else list(ret_on_failure)
                    if len(ret_code):
                        rwcal_status.status = ret_code[0]
                    else:
                        # If it was not explicitly mapped, print the full traceback as this
                        # is not an anticipated error.
                        traceback.print_exc()
                        rwcal_status.status = RwTypes.RwStatus.FAILURE

                    ret_list.insert(0, rwcal_status)
                    return tuple(ret_list)


                rwcal_status.status = RwTypes.RwStatus.SUCCESS
                rwcal_status.traceback = ""
                rwcal_status.error_msg = ""
                ret_list = [rwcal_status]
                if ret is not None:
                    if type(ret) == tuple:
                        ret_list.extend(ret)
                    else:
                        ret_list.append(ret)

                return tuple(ret_list)

            return wrapper

        if isinstance(arg, dict):
            exc_map.update(arg)
            return decorator
        elif ret_on_failure is not None:
            return decorator
        else:
            return decorator(arg)

    return rwstatus
