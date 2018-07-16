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
# Creation Date: 07/27/2016
# 
#

.PHONY : clean

makefile.top := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
TOP_SRC_PATH := $(makefile.top)
TOP_ROOT_PATH := /usr/rift
CMAKE_MODULE_PATH := $(TOP_ROOT_PATH)/cmake/modules

RIFT_BUILD = $(TOP_SRC_PATH)/.build
RIFT_ARTIFACTS = $(TOP_ROOT_PATH)/artifacts
RIFT_INSTALL = $(TOP_ROOT_PATH)
RIFT_SHELL_EXE = $(TOP_ROOT_PATH)/rift-shell -b $(RIFT_BUILD) -i $(RIFT_INSTALL) -a $(RIFT_ARTIFACTS) --standalone-submodule $(TOP_SRC_PATH) --
RELEASE_NUMBER = $(shell git describe | cut -d. -f1 | sed -e 's/^v//')
BUILD_NUMBER = $(shell git describe | cut -d. -f2-)

CONFD = XML_ONLY

BUILD_TYPE = Debug
NOT_DEVELOPER_BUILD ?= FALSE
COVERAGE_BUILD = FALSE
RIFT_AGENT_BUILD = $(CONFD)
PROJECT_TOP_DIR = $(TOP_ROOT_PATH)

all: rw

cmake::
	mkdir -p $(RIFT_BUILD)
	mkdir -p $(RIFT_ARTIFACTS)
	mkdir -p $(RIFT_INSTALL)
	cd $(RIFT_BUILD) && $(RIFT_SHELL_EXE) cmake $(TOP_SRC_PATH) -DCMAKE_INSTALL_PREFIX=$(TOP_ROOT_PATH) -DCMAKE_BUILD_TYPE=$(BUILD_TYPE) -DNOT_DEVELOPER_BUILD=$(NOT_DEVELOPER_BUILD) -DCOVERAGE_BUILD=$(COVERAGE_TYPE) -DRIFT_AGENT_BUILD=$(RIFT_AGENT_BUILD) -DPROJECT_TOP_DIR=$(PROJECT_TOP_DIR) -DCMAKE_MODULE_PATH=${CMAKE_MODULE_PATH} -DRIFT_SUBMODULE_NAME=$(TOP_SRC_PATH) -DRIFT_PACKAGE_GENERATOR=DEB -DRELEASE_NUMBER=$(RELEASE_NUMBER) -DBUILD_NUMBER=$(BUILD_NUMBER)

rw: cmake
	$(RIFT_SHELL_EXE) $(MAKE) -C $(RIFT_BUILD)

package: rw
	$(RIFT_SHELL_EXE) $(MAKE) -C $(RIFT_BUILD) rw.package
install:
	$(RIFT_SHELL_EXE) $(MAKE) -C $(RIFT_BUILD) install

uninstall:
	-xargs -i sh -c '[ -e {} ] && rm -fv {}' < $(RIFT_BUILD)/install_manifest.txt

unittest:
	$(RIFT_SHELL_EXE) $(MAKE) -C $(RIFT_BUILD) rw.unittest

clean:
	@echo "Cleaning up.."
	-rm -rf .build

