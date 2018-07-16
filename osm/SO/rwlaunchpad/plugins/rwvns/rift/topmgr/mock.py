
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

import mock

import gi
gi.require_version('RwcalYang', '1.0')
from gi.repository import RwcalYang

from . import core

import logging

logger = logging.getLogger('rwsdn.mock')

class Mock(core.Topology):
    """This class implements the abstract methods in the Topology class.
    Mock is used for unit testing."""

    def __init__(self):
        super(Mock, self).__init__()

        m = mock.MagicMock()

        create_default_topology()

    def get_network_list(self, account):
        """
        Returns the discovered network

        @param account - a SDN account

        """
        logger.debug("Not yet implemented")
        return None

