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
# Creation Date: 2014/12/11
# 

cmake_minimum_required(VERSION 2.8)

configure_file(
  ${CMAKE_CURRENT_SOURCE_DIR}/generate_tidgen_packages.sh.in
  ${CMAKE_CURRENT_BINARY_DIR}/generate_tidgen_packages.sh
  ESCAPE_QUOTES @ONLY
  )

add_custom_command(
  OUTPUT
    ${CMAKE_CURRENT_BINARY_DIR}/2tidgenMWC_2sriov.tar.gz
    ${CMAKE_CURRENT_BINARY_DIR}/tidgenMWC_2sriov.tar.gz
    ${CMAKE_CURRENT_BINARY_DIR}/2tidgenMWC_4sriov.tar.gz
    ${CMAKE_CURRENT_BINARY_DIR}/tidgenMWC_4sriov.tar.gz
    ${CMAKE_CURRENT_BINARY_DIR}/2tidgenMWC_2sriov_no_ctrlnet.tar.gz
    ${CMAKE_CURRENT_BINARY_DIR}/tidgenMWC_2sriov_no_ctrlnet.tar.gz
    ${CMAKE_CURRENT_BINARY_DIR}/2tidgenMWC_4sriov_no_ctrlnet.tar.gz
    ${CMAKE_CURRENT_BINARY_DIR}/tidgenMWC_4sriov_no_ctrlnet.tar.gz

  COMMAND
    ${CMAKE_CURRENT_BINARY_DIR}/generate_tidgen_packages.sh

  DEPENDS
    mano_yang
    rwcloud_yang
    ${RIFT_SUBMODULE_SOURCE_ROOT}/models/openmano/test/tidgen_ns_2sriov.yaml
    ${RIFT_SUBMODULE_SOURCE_ROOT}/models/openmano/test/tidgen_ns_4sriov.yaml
    ${RIFT_SUBMODULE_SOURCE_ROOT}/models/openmano/test/tidgen_vnf_2sriov.yaml
    ${RIFT_SUBMODULE_SOURCE_ROOT}/models/openmano/test/tidgen_vnf_4sriov.yaml
    ${RIFT_SUBMODULE_SOURCE_ROOT}/models/openmano/test/tidgen_ns_2sriov_no_ctrlnet.yaml
    ${RIFT_SUBMODULE_SOURCE_ROOT}/models/openmano/test/tidgen_ns_4sriov_no_ctrlnet.yaml
    ${RIFT_SUBMODULE_SOURCE_ROOT}/models/openmano/test/tidgen_vnf_2sriov_no_ctrlnet.yaml
    ${RIFT_SUBMODULE_SOURCE_ROOT}/models/openmano/test/tidgen_vnf_4sriov_no_ctrlnet.yaml
    ${RIFT_SUBMODULE_SOURCE_ROOT}/models/openmano/src/openmano2rift.py
  )

add_custom_target(tidgen ALL
  DEPENDS
    mano_yang
    rwcloud_yang
    ${CMAKE_CURRENT_BINARY_DIR}/2tidgenMWC_2sriov.tar.gz
    ${CMAKE_CURRENT_BINARY_DIR}/tidgenMWC_2sriov.tar.gz
    ${CMAKE_CURRENT_BINARY_DIR}/2tidgenMWC_4sriov.tar.gz
    ${CMAKE_CURRENT_BINARY_DIR}/tidgenMWC_4sriov.tar.gz
    ${CMAKE_CURRENT_BINARY_DIR}/2tidgenMWC_2sriov_no_ctrlnet.tar.gz
    ${CMAKE_CURRENT_BINARY_DIR}/tidgenMWC_2sriov_no_ctrlnet.tar.gz
    ${CMAKE_CURRENT_BINARY_DIR}/2tidgenMWC_4sriov_no_ctrlnet.tar.gz
    ${CMAKE_CURRENT_BINARY_DIR}/tidgenMWC_4sriov_no_ctrlnet.tar.gz
  )

install(
  FILES
    ${CMAKE_CURRENT_BINARY_DIR}/2tidgenMWC_4sriov.tar.gz
    ${CMAKE_CURRENT_BINARY_DIR}/tidgenMWC_4sriov.tar.gz
    ${CMAKE_CURRENT_BINARY_DIR}/2tidgenMWC_2sriov.tar.gz
    ${CMAKE_CURRENT_BINARY_DIR}/tidgenMWC_2sriov.tar.gz
    ${CMAKE_CURRENT_BINARY_DIR}/2tidgenMWC_4sriov_no_ctrlnet.tar.gz
    ${CMAKE_CURRENT_BINARY_DIR}/tidgenMWC_4sriov_no_ctrlnet.tar.gz
    ${CMAKE_CURRENT_BINARY_DIR}/2tidgenMWC_2sriov_no_ctrlnet.tar.gz
    ${CMAKE_CURRENT_BINARY_DIR}/tidgenMWC_2sriov_no_ctrlnet.tar.gz

 DESTINATION
    usr/rift/mano/examples/tidgen_ns
    COMPONENT ${INSTALL_COMPONENT}
  )
