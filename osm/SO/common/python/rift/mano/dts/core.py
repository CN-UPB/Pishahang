"""
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

@file core.py
@author Varun Prasad (varun.prasad@riftio.com)
@date 09-Jul-2016

"""

class DtsHandler(object):
    """A common class to hold the barebone objects to build a publisher or
    subscriber
    """
    def __init__(self, log, dts, loop, project):
        """Constructor

        Args:
            log : Log handle
            dts : DTS handle
            loop : Asyncio event loop.
        """
        # Reg handle
        self._reg = None
        self._log = log
        self._dts = dts
        self._loop = loop
        self._project = project

    @property
    def reg(self):
        return self._reg

    @reg.setter
    def reg(self, val):
        self._reg = val

    @property
    def log(self):
        return self._log

    @property
    def dts(self):
        return self._dts

    @property
    def loop(self):
        return self._loop

    @property
    def project(self):
        return self._project

    def deregister(self):
        self._log.debug("De-registering DTS handler ({}) for project {}".
                        format(self.__class__.__name__, self._project))
        if self._reg:
            self._reg.deregister()
            self._reg = None
