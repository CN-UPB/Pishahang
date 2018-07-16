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
# Author(s): Joshua Downer
# Creation Date: 10/01/2015
# 

cmake_minimum_required(VERSION 2.8)

install(
  PROGRAMS
    launchpad.py
    DESTINATION demos
  COMPONENT ${INSTALL_COMPONENT}
  )

install(
  FILES
    pytest/lp_test.py
  DESTINATION
    usr/rift/systemtest/pytest/launchpad
  COMPONENT ${INSTALL_COMPONENT}
  )

install(
  PROGRAMS
    launchpad_recovery
  DESTINATION
    usr/rift/systemtest/launchpad
  COMPONENT ${INSTALL_COMPONENT}
  )

install(
  PROGRAMS
    launchpad
  DESTINATION usr/bin
  COMPONENT ${INSTALL_COMPONENT}
  )

rift_py3test(utest_rwmonitor
  TEST_ARGS
  ${CMAKE_CURRENT_SOURCE_DIR}/utest_rwmonitor.py
  )

rift_py3test(utest_rwnsm
  TEST_ARGS
  ${CMAKE_CURRENT_SOURCE_DIR}/utest_rwnsm.py
  )

rift_py3test(utest_ro_account
  TEST_ARGS
  ${CMAKE_CURRENT_SOURCE_DIR}/utest_ro_account.py
  )

rift_py3test(tosca_ut
  TEST_ARGS
  ${CMAKE_CURRENT_SOURCE_DIR}/tosca_ut.py
  )
