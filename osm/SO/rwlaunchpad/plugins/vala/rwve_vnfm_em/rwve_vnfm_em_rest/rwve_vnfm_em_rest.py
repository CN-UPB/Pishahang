
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

import re
import logging
import rw_status
import rwlogger
import subprocess, os

import gi
gi.require_version('RwVeVnfmEm', '1.0')
gi.require_version('RwTypes', '1.0')
from gi.repository import (
    GObject,
    RwVeVnfmEm,
    RwTypes)

logger = logging.getLogger('rw_ve_vnfm_em.rest')


rwstatus = rw_status.rwstatus_from_exc_map({ IndexError: RwTypes.RwStatus.NOTFOUND,
                                             KeyError: RwTypes.RwStatus.NOTFOUND,
                                             NotImplementedError: RwTypes.RwStatus.NOT_IMPLEMENTED,})

class RwVeVnfmEmRestPlugin(GObject.Object, RwVeVnfmEm.ElementManager):
    """This class implements the Ve-Vnfm VALA methods."""

    def __init__(self):
        GObject.Object.__init__(self)


    @rwstatus
    def do_init(self, rwlog_ctx):
        if not any(isinstance(h, rwlogger.RwLogger) for h in logger.handlers):
            logger.addHandler(rwlogger.RwLogger(subcategory="rwcal-aws",
                                                log_hdl=rwlog_ctx,))
    @rwstatus
    def do_vnf_lifecycle_event(self):
        pass
        
