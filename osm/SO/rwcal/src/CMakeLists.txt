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
# Author(s): Tim Mortsolf
# Creation Date: 05/22/2014
# 

cmake_minimum_required(VERSION 2.8)

add_definitions(-std=gnu99)

add_library(rwcal_api SHARED
  rwcal_py.c)

target_link_libraries(rwcal_api PRIVATE
  rwcal-1.0
  rwcal_yang_gen
  rwlib
  rw_vx_plugin
  peas-1.0)

install(TARGETS rwcal_api LIBRARY DESTINATION usr/lib COMPONENT ${INSTALL_COMPONENT})

install(PROGRAMS rwvim.py DESTINATION usr/bin COMPONENT ${INSTALL_COMPONENT})
