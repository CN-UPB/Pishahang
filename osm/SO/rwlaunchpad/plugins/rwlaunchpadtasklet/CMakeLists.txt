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
# Author(s): Austin Cormier
# Creation Date: 05/15/2015
# 

include(rift_plugin)

set(TASKLET_NAME rwlaunchpad)

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
    rift/tasklets/${TASKLET_NAME}/convert_pkg.py
    rift/tasklets/${TASKLET_NAME}/export.py
    rift/tasklets/${TASKLET_NAME}/extract.py
    rift/tasklets/${TASKLET_NAME}/image.py
    rift/tasklets/${TASKLET_NAME}/message.py
    rift/tasklets/${TASKLET_NAME}/onboard.py
    rift/tasklets/${TASKLET_NAME}/state.py
    rift/tasklets/${TASKLET_NAME}/tasklet.py
    rift/tasklets/${TASKLET_NAME}/tosca.py
    rift/tasklets/${TASKLET_NAME}/uploader.py
  COMPONENT ${INSTALL_COMPONENT}
  PYTHON3_ONLY)

rift_python_install_tree(
  FILES
    rift/package/__init__.py
    rift/package/archive.py
    rift/package/checksums.py
    rift/package/convert.py
    rift/package/handler.py
    rift/package/icon.py
    rift/package/image.py
    rift/package/package.py
    rift/package/script.py
    rift/package/store.py
    rift/package/cloud_init.py
  COMPONENT ${INSTALL_COMPONENT}
  PYTHON3_ONLY)

rift_add_subdirs(test scripts)
