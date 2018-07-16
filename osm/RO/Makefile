.PHONY: all test clean

SHELL := /bin/bash

BRANCH ?= master

all: lib-openvim osm-im
	$(MAKE) clean_build build
	$(MAKE) clean_build package

clean: clean_build
	rm -rf .build openvim IM

clean_build:
	rm -rf build
	find osm_ro -name '*.pyc' -delete
	find osm_ro -name '*.pyo' -delete

prepare:
#	ip install --user --upgrade setuptools
	mkdir -p build/
#	VER1=$(shell git describe | sed -e 's/^v//' |cut -d- -f1); \
#	VER2=$(shell git describe | cut -d- -f2); \
#	VER3=$(shell git describe | cut -d- -f3); \
#	echo "$$VER1.dev$$VER2+$$VER3" > build/RO_VERSION
	cp tox.ini build/
	cp MANIFEST.in build/
	cp requirements.txt build/
	cp README.rst build/
	cp setup.py build/
	cp stdeb.cfg build/
	cp -r osm_ro build/
	cp openmano build/
	cp openmanod build/
	cp -r vnfs build/osm_ro
	cp -r scenarios build/osm_ro
	cp -r instance-scenarios build/osm_ro
	cp -r scripts build/osm_ro
	cp -r database_utils build/osm_ro
	cp LICENSE build/osm_ro

connectors: prepare
	# python-novaclient is required for that
	rm -f build/osm_ro/openmanolinkervimconn.py
	cd build/osm_ro; for i in `ls vimconn_*.py |sed "s/\.py//"` ; do echo "import $$i" >> openmanolinkervimconn.py; done
	python build/osm_ro/openmanolinkervimconn.py 2>&1
	rm -f build/osm_ro/openmanolinkervimconn.py

build: connectors prepare
	python -m py_compile build/osm_ro/*.py
#	cd build && tox -e flake8

lib-openvim:
	$(shell git clone https://osm.etsi.org/gerrit/osm/openvim)
	LIB_BRANCH=$(shell git -C openvim branch -a|grep -oP 'remotes/origin/\K$(BRANCH)'); \
	[ -z "$$LIB_BRANCH" ] && LIB_BRANCH='master'; \
	echo "BRANCH: $(BRANCH)"; \
	echo "LIB_OPENVIM_BRANCH: $$LIB_BRANCH"; \
	git -C openvim checkout $$LIB_BRANCH
	make -C openvim clean lite

osm-im:
	$(shell git clone https://osm.etsi.org/gerrit/osm/IM)
	make -C IM clean all

package: prepare
#	apt-get install -y python-stdeb
	cd build && python setup.py --command-packages=stdeb.command sdist_dsc --with-python2=True
	cd build && cp osm_ro/scripts/python-osm-ro.postinst deb_dist/osm-ro*/debian/
	cd build/deb_dist/osm-ro* && dpkg-buildpackage -rfakeroot -uc -us
	mkdir -p .build
	cp build/deb_dist/python-*.deb .build/

snap:
	echo "Nothing to be done yet"

install:
	dpkg -i IM/deb_dist/python-osm-im*.deb
	dpkg -i openvim/.build/python-lib-osm-openvim*.deb
	dpkg -i .build/python-osm-ro*.deb
	cd .. && \
	OSMLIBOVIM_PATH=`python -c 'import lib_osm_openvim; print lib_osm_openvim.__path__[0]'` || FATAL "lib-osm-openvim was not properly installed" && \
	OSMRO_PATH=`python -c 'import osm_ro; print osm_ro.__path__[0]'` || FATAL "osm-ro was not properly installed" && \
	USER=root DEBIAN_FRONTEND=noninteractive $$OSMRO_PATH/database_utils/install-db-server.sh --updatedb || FATAL "osm-ro db installation failed" && \
	USER=root DEBIAN_FRONTEND=noninteractive $$OSMLIBOVIM_PATH/database_utils/install-db-server.sh -u mano -p manopw -d mano_vim_db --updatedb || FATAL "lib-osm-openvim db installation failed"
	service osm-ro restart

develop: prepare
#	pip install -r requirements.txt
	cd build && ./setup.py develop

test:
	. ./test/basictest.sh -f --insert-bashrc --install-openvim --init-openvim
	. ./test/basictest.sh -f reset add-openvim
	./test/test_RO.py deploy -n mgmt -t osm -i cirros034 -d local-openvim --timeout=30 --failfast
	./test/test_RO.py vim  -t osm  -d local-openvim --timeout=30 --failfast

build-docker-from-source:
	docker build -t osm/openmano -f docker/Dockerfile-local .

run-docker:
	docker-compose -f docker/openmano-compose.yml up

stop-docker:
	docker-compose -f docker/openmano-compose.yml down


