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


cmake_minimum_required(VERSION 2.8)

configure_file(
  ${CMAKE_CURRENT_SOURCE_DIR}/generate_packages.sh.in
  ${CMAKE_CURRENT_BINARY_DIR}/generate_packages.sh
  ESCAPE_QUOTES @ONLY
  )

set(PACKAGE_OUTPUT
  ${CMAKE_CURRENT_BINARY_DIR}/ping_pong_nsd.tar.gz
  ${CMAKE_CURRENT_BINARY_DIR}/ping_vnfd.tar.gz
  ${CMAKE_CURRENT_BINARY_DIR}/pong_vnfd.tar.gz
  ${CMAKE_CURRENT_BINARY_DIR}/ping_pong_nsd_aws.tar.gz
  ${CMAKE_CURRENT_BINARY_DIR}/ping_vnfd_aws.tar.gz
  ${CMAKE_CURRENT_BINARY_DIR}/pong_vnfd_aws.tar.gz
  ${CMAKE_CURRENT_BINARY_DIR}/ping_pong_nsd_with_epa.tar.gz
  ${CMAKE_CURRENT_BINARY_DIR}/ping_vnfd_with_epa.tar.gz
  ${CMAKE_CURRENT_BINARY_DIR}/ping_vnfd_with_vca.tar.gz
  ${CMAKE_CURRENT_BINARY_DIR}/pong_vnfd_with_vca.tar.gz
  ${CMAKE_CURRENT_BINARY_DIR}/ping_pong_nsd_with_vca.tar.gz
  ${CMAKE_CURRENT_BINARY_DIR}/pong_vnfd_with_epa.tar.gz
  ${CMAKE_CURRENT_BINARY_DIR}/ping_vnfd_with_vip.tar.gz
  ${CMAKE_CURRENT_BINARY_DIR}/pong_vnfd_with_vip.tar.gz
  ${CMAKE_CURRENT_BINARY_DIR}/ping_pong_nsd_with_vip.tar.gz
  ${CMAKE_CURRENT_BINARY_DIR}/ping_vnfd_with_image.tar.gz
  ${CMAKE_CURRENT_BINARY_DIR}/pong_vnfd_with_image.tar.gz
  ${CMAKE_CURRENT_BINARY_DIR}/ping_vnfd_with_vca.tar.gz
  ${CMAKE_CURRENT_BINARY_DIR}/pong_vnfd_with_vca.tar.gz
  ${CMAKE_CURRENT_BINARY_DIR}/ping_pong_nsd_with_vca.tar.gz
  ${CMAKE_CURRENT_BINARY_DIR}/ping_vnfd_with_image.tar.gz
  ${CMAKE_CURRENT_BINARY_DIR}/pong_vnfd_with_image.tar.gz
  ${CMAKE_CURRENT_BINARY_DIR}/ping_vnfd_with_vnf_input_parameters.tar.gz
  ${CMAKE_CURRENT_BINARY_DIR}/pong_vnfd_with_vnf_input_parameters.tar.gz
  ${CMAKE_CURRENT_BINARY_DIR}/ping_pong_nsd_with_vnf_input_parameters.tar.gz)

add_custom_command(
    OUTPUT ${PACKAGE_OUTPUT}
    COMMAND ${CMAKE_CURRENT_BINARY_DIR}/generate_packages.sh
    DEPENDS
       mano_yang
       rwcloud_yang
       ${CMAKE_CURRENT_SOURCE_DIR}/ping_pong_nsd.py
       ${CMAKE_CURRENT_SOURCE_DIR}/rift/mano/examples/ping_setup.py
       ${CMAKE_CURRENT_SOURCE_DIR}/rift/mano/examples/ping_rate.py
       ${CMAKE_CURRENT_SOURCE_DIR}/rift/mano/examples/ping_start_stop.py
       ${CMAKE_CURRENT_SOURCE_DIR}/rift/mano/examples/pong_setup.py
       ${CMAKE_CURRENT_SOURCE_DIR}/rift/mano/examples/pong_start_stop.py
       ${CMAKE_CURRENT_SOURCE_DIR}/rift/mano/examples/ping_initial_config.py
       ${CMAKE_CURRENT_SOURCE_DIR}/rift/mano/examples/pong_initial_config.py
       ${CMAKE_CURRENT_SOURCE_DIR}/rift/mano/examples/start_traffic.py
       ${CMAKE_CURRENT_SOURCE_DIR}/rift/mano/examples/stop_traffic.py
       ${CMAKE_CURRENT_SOURCE_DIR}/rift/mano/examples/primitive_test.py
  )

add_custom_target(ping_pong_pkg_gen ALL
    DEPENDS mano_yang rwcloud_yang ${PACKAGE_OUTPUT}
  )

install(
    FILES ${PACKAGE_OUTPUT}
    DESTINATION
      usr/rift/mano/examples/ping_pong_ns
      COMPONENT ${INSTALL_COMPONENT}
    )

rift_python_install_tree(
  COMPONENT ${INSTALL_COMPONENT}
  FILES
    rift/mano/examples/ping_pong_nsd.py
    rift/mano/examples/ping_setup.py
    rift/mano/examples/ping_start_stop.py
    rift/mano/examples/pong_setup.py
    rift/mano/examples/pong_start_stop.py
    rift/mano/examples/start_traffic.py
    rift/mano/examples/ping_set_rate.py
    rift/mano/examples/stop_traffic.py
    rift/mano/examples/ping_initial_config.py
    rift/mano/examples/pong_initial_config.py
    rift/mano/examples/ping_set_rate.py
    rift/mano/examples/primitive_test.py
  )

install(
  PROGRAMS
    rift/mano/examples/ping_scale.py
    stand_up_ping_pong
  DESTINATION usr/bin
  COMPONENT ${INSTALL_COMPONENT}
  )

