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
# Creation Date: 2016/07/01
#

include(rift_plugin)

set(TASKLET_NAME rwpkgmgr)

##
# This function creates an install target for the plugin artifacts
##
rift_install_gobject_python_plugin(${TASKLET_NAME} ${TASKLET_NAME}.py COMPONENT ${INSTALL_COMPONENT})

# Workaround RIFT-6485 - rpmbuild defaults to python2 for
# anything not in a site-packages directory so we have to
# install the plugin implementation in site-packages and then
# import it from the actual plugin.
rift_python_install_tree(
  FILES
    rift/tasklets/${TASKLET_NAME}/__init__.py
    rift/tasklets/${TASKLET_NAME}/${TASKLET_NAME}.py
    rift/tasklets/${TASKLET_NAME}/rpc.py
    rift/tasklets/${TASKLET_NAME}/downloader/__init__.py
    rift/tasklets/${TASKLET_NAME}/downloader/url.py
    rift/tasklets/${TASKLET_NAME}/downloader/copy.py
    rift/tasklets/${TASKLET_NAME}/proxy/__init__.py
    rift/tasklets/${TASKLET_NAME}/proxy/base.py
    rift/tasklets/${TASKLET_NAME}/proxy/filesystem.py
    rift/tasklets/${TASKLET_NAME}/publisher/__init__.py
    rift/tasklets/${TASKLET_NAME}/publisher/download_status.py
    rift/tasklets/${TASKLET_NAME}/publisher/copy_status.py
    rift/tasklets/${TASKLET_NAME}/subscriber/__init__.py
    rift/tasklets/${TASKLET_NAME}/subscriber/download_status.py
  COMPONENT ${INSTALL_COMPONENT}
  PYTHON3_ONLY)

rift_add_subdirs(test)
