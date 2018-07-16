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
# Author(s): Anil Gunturu
# Creation Date: 03/26/2014
# 

##
# DEPENDENCY ALERT
# The submodule dependencies must be specified in the
# .gitmodules.dep file at the top level (supermodule) directory
# If this submodule depends other submodules remember to update
# the .gitmodules.dep
##

cmake_minimum_required(VERSION 2.8)

message(CMAKE_MODULE_PATH=${CMAKE_MODULE_PATH})

##
# DO NOT add any code before this and DO NOT
# include this file anywhere else
##
include(rift_submodule NO_POLICY_SCOPE)
include(rift_python)

##
# Submodule specific includes will go here, 
# These are specified here, since these variables are accessed
# from multiple sub directories. If the variable is subdirectory
# specific it must be declared in the subdirectory.
##

# Default package
set(INSTALL_COMPONENT mano)

option(PRODUCT "Control the details of the build" OSM)

if (PRODUCT STREQUAL "RIFTWARE")
set(INCLUDE_EXAMPLES ON)
else()
set(INCLUDE_EXAMPLES OFF)
endif()

##
# Include the subdirs
##
set(subdirs
  common
  models
  rwcal
  rwmon
  rwcm
  rwlaunchpad
  rwprojectmano
  )

if (NOT RIFT_AGENT_BUILD STREQUAL "XML_ONLY")
  list(APPEND subdirs confd_client)
endif()

if (INCLUDE_EXAMPLES)
   message("Including examples")
   list(APPEND subdirs examples)
else()
   message("NOT including examples")
endif()

rift_add_subdirs(SUBDIR_LIST ${subdirs})

install(FILES BUILD.sh DESTINATION bin COMPONENT installer)

##
# Set up package details
##

rift_set_component_package_fields(
  "mano"
  DESCRIPTION "RIFT.ware MANO"
  )

rift_set_component_package_fields(
  "rwcal-plugin-aws"
  DESCRIPTION "RIFT.ware AWS plugin"
  )

rift_set_component_package_fields(
  "rwcal-plugin-cloudsim"
  DESCRIPTION "RIFT.ware cloudsim plugin"
  )

rift_set_component_package_fields(
  "rwcal-plugin-cloudsimproxy"
  DESCRIPTION "RIFT.ware cloudsimproxy plugin"
  )

rift_set_component_package_fields(
  "rwcal-plugin-openmano-vimconnector"
  DESCRIPTION "RIFT.ware vimconnector plugin"
  )

rift_set_component_package_fields(
  "rwcal-plugin-openstack"
  DESCRIPTION "RIFT.ware openstack plugin"
  )

rift_set_component_package_fields(
  "rwcal-plugin-kubernetes"
  DESCRIPTION "RIFT.ware kubernetes plugin"
  )

rift_set_component_package_fields(
  "rwcal-plugin-brocade"
  DESCRIPTION "RIFT.ware brocade plugin"
  )

rift_set_component_package_fields(
  "rwcal-plugin-mock"
  DESCRIPTION "RIFT.ware mock plugin"
  )

##
# This macro adds targets for documentaion, unittests, code coverage and packaging
##
rift_add_submodule_targets(SUBMODULE_PACKAGE_NAME "rw.core.mano")

# Workaround whatever mess rw.package is doing as it can't seem
# to figure out that it should make a directory -before- making
# symlinks..
set(dir usr/lib64/python${RIFT_PYTHON3}/site-packages/gi/overrides)
install(FILES
  ${CMAKE_CURRENT_SOURCE_DIR}/.cpack-workaround
  DESTINATION ${dir})

if (RIFT_SUPPORT_PYTHON2)
  set(dir usr/lib64/python${RIFT_PYTHON2}/site-packages/gi/overrides)

  install(FILES
    ${CMAKE_CURRENT_SOURCE_DIR}/.cpack-workaround
    DESTINATION ${dir})
endif()
