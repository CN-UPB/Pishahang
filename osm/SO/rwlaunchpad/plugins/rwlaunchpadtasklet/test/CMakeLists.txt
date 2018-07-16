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
# Creation Date: 04/22/2016
# 

rift_py3test(utest_serializer
  TEST_ARGS
  ${CMAKE_CURRENT_SOURCE_DIR}/utest_serializer.py
  )

rift_py3test(utest_export
  TEST_ARGS
  ${CMAKE_CURRENT_SOURCE_DIR}/utest_export.py
  )

rift_py3test(utest_onboard
  TEST_ARGS
  ${CMAKE_CURRENT_SOURCE_DIR}/utest_onboard.py
  )

rift_py3test(utest_package.py
  TEST_ARGS
  ${CMAKE_CURRENT_SOURCE_DIR}/utest_package.py
  )

rift_py3test(utest_uploader_app_dts.create.py
  TEST_ARGS
  ${CMAKE_CURRENT_SOURCE_DIR}/utest_uploader_app_dts.py TestCase.test_package_create_rpc
  )

rift_py3test(utest_uploader_app_dts.export.py
  TEST_ARGS
  ${CMAKE_CURRENT_SOURCE_DIR}/utest_uploader_app_dts.py TestCase.test_package_export
  )
