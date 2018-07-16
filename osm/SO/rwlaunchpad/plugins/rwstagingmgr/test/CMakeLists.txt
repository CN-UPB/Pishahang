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
# Creation Date: 28/09/2016
#

##
# utest_publisher_dts
##
rift_py3test(rwstg_utest_publisher_dts.test_download_publisher
  TEST_ARGS
  ${CMAKE_CURRENT_SOURCE_DIR}/utest_publisher_dts.py TestCase.test_download_publisher
  )

rift_py3test(rwstg_utest_publisher_dts.test_publish
  TEST_ARGS
  ${CMAKE_CURRENT_SOURCE_DIR}/utest_publisher_dts.py TestCase.test_publish
  )


add_custom_target(rwstg_utest_publisher_dts.py
  DEPENDS
    rwstg_utest_publisher_dts.test_download_publisher
    rwstg_utest_publisher_dts.test_publish
  )

##
# utest_rpc_dts.py
##
rift_py3test(rwstg_utest_rpc_dts.test_staging_area_create
  TEST_ARGS
  ${CMAKE_CURRENT_SOURCE_DIR}/utest_rpc_dts.py TestCase.test_staging_area_create
  )

add_custom_target(rwstg_utest_rpc_dts.py
  DEPENDS
    rwstg_utest_rpc_dts.test_staging_area_create
  )

##
# utest_staging_store.py
##
rift_py3test(rwstg_utest_staging_store.py
  TEST_ARGS
  ${CMAKE_CURRENT_SOURCE_DIR}/utest_staging_store.py
  )

##
# utest_tornado_app.py
##
rift_py3test(rwstg_utest_tornado_app.py
  TEST_ARGS
  ${CMAKE_CURRENT_SOURCE_DIR}/utest_tornado_app.py
  )

add_custom_target(rwstagingmgmt_test
  DEPENDS
    rwstg_utest_staging_store.py
    rwstg_utest_publisher_dts.py
    rwstg_utest_rpc_dts.py
    rwstg_utest_tornado_app.py
  )
