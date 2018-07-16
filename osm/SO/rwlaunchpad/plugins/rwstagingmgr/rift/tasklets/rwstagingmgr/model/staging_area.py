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
# Author(s): Varun Prasad
# Creation Date: 09/28/2016
#


import time

import gi
gi.require_version('RwStagingMgmtYang', '1.0')
from gi.repository import (
        RwStagingMgmtYang,
        )


class StagingArea(object):
    """A pythonic wrapper around the GI object StagingArea
    """
    def __init__(self, model=None):
        self._model = model
        if not self._model:
            self._model = RwStagingMgmtYang.YangData_RwProject_Project_StagingAreas_StagingArea.from_dict({})

    @property
    def area_id(self):
        return self._model.area_id

    @property
    def model(self):
        return self._model

    @property
    def project_name(self):
        return self._model.project_name

    @property
    def has_expired(self):
        current_time = time.time()
        expiry_time = self.model.created_time + self.model.validity_time
        if expiry_time <= current_time:
            return True
        return False

    def as_dict(self):
        return self._model.as_dict()
