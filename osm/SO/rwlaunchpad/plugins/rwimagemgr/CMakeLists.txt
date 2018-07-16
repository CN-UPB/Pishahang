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
# Creation Date: 2016/06/23
# 

include(rift_plugin)

set(TASKLET_NAME rwimagemgrtasklet)

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
    rift/tasklets/rwimagemgr/__init__.py
    rift/tasklets/rwimagemgr/glance_client.py
    rift/tasklets/rwimagemgr/glance_proxy_server.py
    rift/tasklets/rwimagemgr/tasklet.py
    rift/tasklets/rwimagemgr/upload.py
    rift/tasklets/rwimagemgr/lib/__init__.py
    rift/tasklets/rwimagemgr/lib/quickproxy/__init__.py
    rift/tasklets/rwimagemgr/lib/quickproxy/proxy.py
  COMPONENT ${INSTALL_COMPONENT}
  PYTHON3_ONLY)

rift_python_install_tree(
  FILES
    rift/imagemgr/__init__.py
    rift/imagemgr/client.py
  COMPONENT ${INSTALL_COMPONENT}
  PYTHON3_ONLY)

install(
    PROGRAMS
        bin/glance_start_wrapper
    DESTINATION
        usr/bin
  COMPONENT ${INSTALL_COMPONENT}
    )

if($ENV{RIFT_PLATFORM} MATCHES "fc20")
  install(
      FILES
          etc/fc20/glance-api.conf
          etc/fc20/glance-registry.conf
          etc/fc20/glance-scrubber.conf
          etc/fc20/glance-cache.conf
          etc/fc20/policy.json
          etc/fc20/schema-image.json
          etc/fc20/glance-api-dist-paste.ini
      DESTINATION
          etc/glance
      COMPONENT ${INSTALL_COMPONENT}
      )
elseif($ENV{RIFT_PLATFORM} MATCHES "ub16")
  install(
      FILES
          etc/ub16/glance-api.conf
          etc/ub16/glance-api-paste.ini
          etc/ub16/glance-registry.conf
          etc/ub16/glance-registry-paste.ini
          etc/ub16/glance-cache.conf
          etc/ub16/glance-manage.conf
          etc/ub16/policy.json
          etc/ub16/schema-image.json
      DESTINATION
          etc/glance
      COMPONENT ${INSTALL_COMPONENT}
      )
else()
    message(FATAL_ERROR "Unknown platform $ENV{RIFT_PLATFORM}")
endif()

rift_add_subdirs(test)
