#!/usr/bin/env bash
# 
#   Copyright 2016,2017 RIFT.IO Inc
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
# Author(s): Jeremy Mordkoff, Lezz Giles
# Creation Date: 08/29/2016
# 
#

# BUILD.sh
#
# This is a top-level build script for OSM SO or UI
#
# Arguments and options: use -h or --help
#
# dependencies -- requires sudo rights

MODULE=SO

# Defensive bash programming flags
set -o errexit    # Exit on any error
trap 'echo ERROR: Command failed: \"$BASH_COMMAND\"' ERR
set -o nounset    # Expanding an unset variable is an error.  Variables must be
                  # set before they can be used.

###############################################################################
# Options and arguments

# There 
params="$(getopt -o h -l install,help --name "$0" -- "$@")"
if [ $? != 0 ] ; then echo "Failed parsing options." >&2 ; exit 1 ; fi

eval set -- $params

installFromPackages=false

while true; do
    case "$1" in
	--install) installFromPackages=true; shift;;
	-h|--help)
	    echo
	    echo "NAME:"
	    echo "  $0"
	    echo
	    echo "SYNOPSIS:"
	    echo "  $0 -h|--help"
	    echo "  $0 [--install] [PLATFORM_REPOSITORY] [PLATFORM_VERSION]"
	    echo
	    echo "DESCRIPTION:"
	    echo "  Prepare current system to run $MODULE.  By default, the system"
	    echo "  is set up to support building $MODULE; optionally, "
	    echo "  $MODULE can be installed from a Debian package repository."
	    echo
	    echo "  --install:  install $MODULE from package"
	    echo "  PLATFORM_REPOSITORY (optional): name of the RIFT.ware repository."
	    echo "  PLATFORM_VERSION (optional): version of the platform packages to be installed."
	    echo
	    exit 0;;
	--) shift; break;;
	*) echo "Not implemented: $1" >&2; exit 1;;
    esac
done

# Turn this on after handling options, so the output doesn't get cluttered.
set -x             # Print commands before executing them

###############################################################################
# Set up repo and version

PLATFORM_REPOSITORY=${1:-OSM3}
PLATFORM_VERSION=${2:-5.2.0.2.72254}

###############################################################################
# Main block

# must be run from the top of a workspace
cd $(dirname $0)

# enable the right repos
curl http://repos.riftio.com/public/xenial-riftware-public-key | sudo apt-key add -

# always use the same file name so that updates will overwrite rather than enable a second repo
sudo curl -o /etc/apt/sources.list.d/rift.list http://buildtracker.riftio.com/repo_file/ub16/${PLATFORM_REPOSITORY}/ 
sudo apt-get update

sudo apt install -y --allow-downgrades rw.tools-container-tools=${PLATFORM_VERSION} rw.tools-scripts=${PLATFORM_VERSION}

if $installFromPackages; then
    
    # Install module and platform from packages
    sudo -H /usr/rift/container_tools/mkcontainer --modes $MODULE --repo ${PLATFORM_REPOSITORY} --rw-version ${PLATFORM_VERSION}
    
else

    # Install environment to build module
    sudo -H /usr/rift/container_tools/mkcontainer --modes $MODULE-dev --repo ${PLATFORM_REPOSITORY} --rw-version ${PLATFORM_VERSION}
    sudo -H pip3 install --upgrade pip
    sudo -H pip3 install setuptools 
    sudo -H pip3 install juju 
    sudo mkdir -p /usr/rift/etc/default
    sudo chmod 777 /usr/rift/etc/default
    echo LAUNCHPAD_OPTIONS="--use-xml-mode" >> /usr/rift/etc/default/launchpad
    sudo systemctl daemon-reload || true

    IM_FILES="
ietf-l2-topology.yang
ietf-network-topology.yang
ietf-network.yang
mano-rift-groupings.yang
mano-types.yang
nsd-base.yang
nsd.yang
nsr.yang
odl-network-topology.yang
project-nsd.yang
project-vnfd.yang
vlr.yang
vnfd-base.yang
vnfd.yang
vnffgd.yang
vnfr.yang
"
    echo "installing IM files"
    if [ ! -d ../IM ]; then
        echo cloning IM
        # note that this cannot be inside the SO or else CMAKE will find it 
        git clone $(dirname $(git remote get-url origin))/IM.git ../IM
    fi
    for file in $IM_FILES; do 
        rm -f models/plugins/yang/$file
        cp ../IM/models/yang/$file models/plugins/yang
    done

    # Build  and install module
    make -j16 
    sudo make install

fi

if [[ $MODULE == SO ]]; then
    echo "Creating Service ...."
    sudo /usr/rift/bin/create_launchpad_service
fi


