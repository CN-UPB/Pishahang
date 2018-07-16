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

@file conftest.py
@author Varun Prasad (varun.prasad@riftio.com)
@date 21/01/2016

"""

def pytest_addoption(parser):
    # Openstack related options
    parser.addoption("--os-host", action="store", default="10.66.4.102")
    parser.addoption("--os-user", action="store", default="pluto")
    parser.addoption("--os-password", action="store", default="mypasswd")
    parser.addoption("--os-tenant", action="store", default="demo")
    parser.addoption("--os-network", action="store", default="private")

    # aws related options
    parser.addoption("--aws-user", action="store", default="AKIAIKRDX7BDLFU37PDA")
    parser.addoption("--aws-password", action="store", default="cjCRtJxVylVkbYvOUQeyvCuOWAHieU6gqcQw29Hw")
    parser.addoption("--aws-region", action="store", default="us-east-1")
    parser.addoption("--aws-zone", action="store", default="us-east-1c")
    parser.addoption("--aws-ssh-key", action="store", default="vprasad-sshkey")
