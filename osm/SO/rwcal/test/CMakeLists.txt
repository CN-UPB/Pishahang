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
# Creation Date: 06/27/2014
# 

cmake_minimum_required(VERSION 2.8)

set(subdirs cal_module_test)
rift_add_subdirs(SUBDIR_LIST ${subdirs})

# rift_gtest(unittest_rwcal_cloud
#   TEST_SRCS rwcal_cloud_gtest.cpp
#   TEST_LIBS
#     rwcal_api
#     rwcal_yang_gen
# )

rift_gtest(unittest_rwcal_callback
  TEST_SRCS rwcal_callback_gtest.cpp
  TEST_LIBS
    rwcal-1.0
    rwcal_api
)

##
# Add the basic plugin python test
##
#rift_py3test(openstack_cal_tests
#  LONG_UNITTEST_TARGET
#  TEST_ARGS -m pytest --junit-xml=${RIFT_UNITTEST_DIR}/openstack_cal/unittest.xml #${CMAKE_CURRENT_SOURCE_DIR}/test_rwcal_openstack_pytest.py
#)


add_executable(rwcal_dump rwcal_dump.cpp)
target_link_libraries(rwcal_dump
  rwcal_api
  rwlib
  rwyang
  rwcal_yang_gen
  CoreFoundation
  glib-2.0
  protobuf-c
)

# added for 4.0
install(
  FILES 
    RIFT.ware-ready.py 
    openstack_resources.py
  DESTINATION usr/bin
  COMPONENT ${INSTALL_COMPONENT}
)

