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
# Author(s): Paul Laidler
# Creation Date: 2016/01/04
#

import rift.vcs.vcs
import time
import gi

def test_launchpad_longevity(mgmt_session, mgmt_domain_name):
    time.sleep(60)
    rift.vcs.vcs.wait_until_system_started(mgmt_session)

