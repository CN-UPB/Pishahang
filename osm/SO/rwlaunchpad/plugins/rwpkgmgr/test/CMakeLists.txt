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
# utest_pkgmgr_subscriber_dts
##
rift_py3test(utest_pkgmgr_subscriber_dts.py
  TEST_ARGS
  ${CMAKE_CURRENT_SOURCE_DIR}/utest_pkgmgr_subscriber_dts.py
  )

##
# utest_pkgmgr_publisher_dts
##
rift_py3test(utest_pkgmgr_publisher_dts.test_download_publisher
  TEST_ARGS
  ${CMAKE_CURRENT_SOURCE_DIR}/utest_pkgmgr_publisher_dts.py TestCase.test_download_publisher
  )

rift_py3test(utest_pkgmgr_publisher_dts.test_publish
  TEST_ARGS
  ${CMAKE_CURRENT_SOURCE_DIR}/utest_pkgmgr_publisher_dts.py TestCase.test_publish
  )

rift_py3test(utest_pkgmgr_publisher_dts.test_url_download
  TEST_ARGS
  ${CMAKE_CURRENT_SOURCE_DIR}/utest_pkgmgr_publisher_dts.py TestCase.test_url_download
  )

rift_py3test(utest_pkgmgr_publisher_dts.test_url_download_unreachable_ip
  TEST_ARGS
  ${CMAKE_CURRENT_SOURCE_DIR}/utest_pkgmgr_publisher_dts.py TestCase.test_url_download_unreachable_ip
  )

rift_py3test(utest_pkgmgr_publisher_dts.test_cancelled
  TEST_ARGS
  ${CMAKE_CURRENT_SOURCE_DIR}/utest_pkgmgr_publisher_dts.py TestCase.test_cancelled
  )

add_custom_target(utest_pkgmgr_publisher_dts.py
  DEPENDS
    utest_pkgmgr_publisher_dts.test_download_publisher
    utest_pkgmgr_publisher_dts.test_publish
    utest_pkgmgr_publisher_dts.test_url_download
    utest_pkgmgr_publisher_dts.test_url_download_unreachable_ip
    utest_pkgmgr_publisher_dts.test_cancelled
  )

##
# utest_filesystem_proxy_dts.py
##
rift_py3test(utest_filesystem_proxy.test_endpoint_discovery
  TEST_ARGS
  ${CMAKE_CURRENT_SOURCE_DIR}/utest_filesystem_proxy_dts.py TestCase.test_endpoint_discovery
  )

rift_py3test(utest_filesystem_proxy.test_schema_rpc
  TEST_ARGS
  ${CMAKE_CURRENT_SOURCE_DIR}/utest_filesystem_proxy_dts.py TestCase.test_schema_rpc
  )

rift_py3test(utest_filesystem_proxy.test_file_proxy_rpc
  TEST_ARGS
  ${CMAKE_CURRENT_SOURCE_DIR}/utest_filesystem_proxy_dts.py TestCase.test_file_proxy_rpc
  )

rift_py3test(utest_filesystem_proxy.test_file_add_workflow
  TEST_ARGS
  ${CMAKE_CURRENT_SOURCE_DIR}/utest_filesystem_proxy_dts.py TestCase.test_file_add_workflow
  )

rift_py3test(utest_filesystem_proxy.test_file_delete_workflow
  TEST_ARGS
  ${CMAKE_CURRENT_SOURCE_DIR}/utest_filesystem_proxy_dts.py TestCase.test_file_delete_workflow
  )

add_custom_target(utest_filesystem_proxy_dts.py
  DEPENDS
    utest_filesystem_proxy.test_endpoint_discovery
    utest_filesystem_proxy.test_schema_rpc
    utest_filesystem_proxy.test_file_proxy_rpc
    utest_filesystem_proxy.test_file_add_workflow
    utest_filesystem_proxy.test_file_delete_workflow
  )

add_custom_target(rwpkgmgmt_test
  DEPENDS
    utest_filesystem_proxy_dts.py
    utest_pkgmgr_publisher_dts.py
    utest_pkgmgr_subscriber_dts.py
  )
