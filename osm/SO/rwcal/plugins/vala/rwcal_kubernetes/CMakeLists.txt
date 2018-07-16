
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

include(rift_plugin)

### rwcal-kubernetes package
set(INSTALL_COMPONENT rwcal-plugin-kubernetes)

rift_install_gobject_python_plugin(rwcal_kubernetes rwcal_kubernetes.py COMPONENT ${INSTALL_COMPONENT})

rift_python_install_tree(
  FILES
    rift/rwcal/kubernetes/__init__.py
    rift/rwcal/kubernetes/kubernetes_drv.py
    
  PYTHON3_ONLY
  COMPONENT ${INSTALL_COMPONENT})

