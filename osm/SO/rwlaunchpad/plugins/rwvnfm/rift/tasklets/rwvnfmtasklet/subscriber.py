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

import rift.mano.dts as mano_dts
import asyncio

from gi.repository import (
    RwDts as rwdts,
    RwTypes,
    RwVlrYang,
    RwYang
    )
import rift.tasklets

import requests


class VlrSubscriberDtsHandler(mano_dts.AbstractOpdataSubscriber):
    """ VLR  DTS handler """
    XPATH = "D,/vlr:vlr-catalog/vlr:vlr"

    def __init__(self, log, dts, loop, project, callback=None):
        super().__init__(log, dts, loop, project, callback)

    def get_xpath(self):
        return ("D,/vlr:vlr-catalog/vlr:vlr")
