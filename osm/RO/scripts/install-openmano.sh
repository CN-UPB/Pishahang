#!/bin/bash

##
# Copyright 2015 Telefónica Investigación y Desarrollo, S.A.U.
# This file is part of openmano
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# For those usages not covered by the Apache License, Version 2.0 please
# contact with: nfvlabs@tid.es
##

#ONLY TESTED in Ubuntu 16.04   partially tested in Ubuntu 14.10 14.04 16.04, CentOS7 and RHEL7
#Get needed packages, source code and configure to run openmano
#Ask for database user and password if not provided

function usage(){
    echo -e "usage: sudo -E $0 [OPTIONS]"
    echo -e "Install last stable source code in ./openmano and the needed packages"
    echo -e "On a Ubuntu 16.04 it configures openmano as a service"
    echo -e "  OPTIONS"
    echo -e "     -u USER:    database admin user. 'root' by default. Prompts if needed"
    echo -e "     -p PASS:    database admin password to be used or installed. Prompts if needed"
    echo -e "     -q --quiet: install in unattended mode"
    echo -e "     -h --help:  show this help"
    echo -e "     -b REFSPEC: install from source code using a specific branch (master, v2.0, ...) or tag"
    echo -e "                    -b master          (main RO branch)"
    echo -e "                    -b v2.0            (v2.0 branch)"
    echo -e "                    -b tags/v1.1.0     (a specific tag)"
    echo -e "                    ..."
    echo -e "     --develop:  install last version for developers, and do not configure as a service"
    echo -e "     --forcedb:  reinstall mano_db DB, deleting previous database if exists and creating a new one"
    echo -e "     --updatedb: do not reinstall mano_db DB if it exists, just update database"
    echo -e "     --force:    makes idenpotent, delete previous installations folders if needed. It assumes --updatedb if --forcedb option is not provided"
    echo -e "     --noclone:  assumes that openmano was cloned previously and that this script is run from the local repo"
    echo -e "     --no-install-packages: use this option to skip updating and installing the requires packages. This avoid wasting time if you are sure requires packages are present e.g. because of a previous installation"
    echo -e "     --no-db: do not install mysql server"
}

function install_packages(){
    [ -x /usr/bin/apt-get ] && apt-get install -y $*
    [ -x /usr/bin/yum ]     && yum install     -y $*   
    
    #check properly installed
    for PACKAGE in $*
    do
        PACKAGE_INSTALLED="no"
        [ -x /usr/bin/apt-get ] && dpkg -l $PACKAGE            &>> /dev/null && PACKAGE_INSTALLED="yes"
        [ -x /usr/bin/yum ]     && yum list installed $PACKAGE &>> /dev/null && PACKAGE_INSTALLED="yes" 
        if [ "$PACKAGE_INSTALLED" = "no" ]
        then
            echo "failed to install package '$PACKAGE'. Revise network connectivity and try again" >&2
            exit 1
       fi
    done
}

function ask_user(){
    # ask to the user and parse a response among 'y', 'yes', 'n' or 'no'. Case insensitive
    # Params: $1 text to ask;   $2 Action by default, can be 'y' for yes, 'n' for no, other or empty for not allowed
    # Return: true(0) if user type 'yes'; false (1) if user type 'no'
    read -e -p "$1" USER_CONFIRMATION
    while true ; do
        [ -z "$USER_CONFIRMATION" ] && [ "$2" == 'y' ] && return 0
        [ -z "$USER_CONFIRMATION" ] && [ "$2" == 'n' ] && return 1
        [ "${USER_CONFIRMATION,,}" == "yes" ] || [ "${USER_CONFIRMATION,,}" == "y" ] && return 0
        [ "${USER_CONFIRMATION,,}" == "no" ]  || [ "${USER_CONFIRMATION,,}" == "n" ] && return 1
        read -e -p "Please type 'yes' or 'no': " USER_CONFIRMATION
    done
}

GIT_URL=https://osm.etsi.org/gerrit/osm/RO.git
GIT_OVIM_URL=https://osm.etsi.org/gerrit/osm/openvim.git
GIT_OSMIM_URL=https://osm.etsi.org/gerrit/osm/IM.git
DBUSER="root"
DBPASSWD=""
DBPASSWD_PARAM=""
QUIET_MODE=""
DEVELOP=""
DB_FORCE_UPDATE=""
UPDATEDB=""
FORCE=""
NOCLONE=""
NO_PACKAGES=""
NO_DB=""
COMMIT_ID=""

while getopts ":u:p:b:hiq-:" o; do
    case "${o}" in
        u)
            export DBUSER="$OPTARG"
            ;;
        p)
            export DBPASSWD="$OPTARG"
            export DBPASSWD_PARAM="-p$OPTARG"
            ;;
        b)
            export COMMIT_ID=${OPTARG}
            ;;
        q)
            export QUIET_MODE=yes
            export DEBIAN_FRONTEND=noninteractive
            ;;
        h)
            usage && exit 0
            ;;
        -)
            [ "${OPTARG}" == "help" ] && usage && exit 0
            [ "${OPTARG}" == "develop" ] && DEVELOP="y" && continue
            [ "${OPTARG}" == "forcedb" ] && DB_FORCE_UPDATE="${DB_FORCE_UPDATE}--forcedb" && continue
            [ "${OPTARG}" == "updatedb" ] && DB_FORCE_UPDATE="${DB_FORCE_UPDATE}--updatedb" && continue
            [ "${OPTARG}" == "force" ]   &&  FORCE="y" && continue
            [ "${OPTARG}" == "noclone" ] && NOCLONE="y" && continue
            [ "${OPTARG}" == "quiet" ] && export QUIET_MODE=yes && export DEBIAN_FRONTEND=noninteractive && continue
            [ "${OPTARG}" == "no-install-packages" ] && export NO_PACKAGES=yes && continue
            [ "${OPTARG}" == "no-db" ] && NO_DB="y" && continue
            echo -e "Invalid option: '--$OPTARG'\nTry $0 --help for more information" >&2
            exit 1
            ;;
        \?)
            echo -e "Invalid option: '-$OPTARG'\nTry $0 --help for more information" >&2
            exit 1
            ;;
        :)
            echo -e "Option '-$OPTARG' requires an argument\nTry $0 --help for more information" >&2
            exit 1
            ;;
        *)
            usage >&2
            exit 1
            ;;
    esac
done

if [ "$DB_FORCE_UPDATE" == "--forcedb--updatedb" ] || [ "$DB_FORCE_UPDATE" == "--updatedb--forcedb" ] ; then
    echo "Error: options --forcedb and --updatedb are mutually exclusive" >&2
    exit 1
elif [ -n "$FORCE" ] && [ -z "$DB_FORCE_UPDATE" ] ; then
    DB_FORCE_UPDATE="--updatedb"
fi

#check root privileges and non a root user behind
[ "$USER" != "root" ] && echo "Needed root privileges" >&2 && exit 1
if [[ -z "$SUDO_USER" ]] || [[ "$SUDO_USER" = "root" ]]
then
    [[ -z $QUIET_MODE ]] && ! ask_user "Install in the root user (y/N)? " n  && echo "Cancelled" && exit 1
    export SUDO_USER=root
fi

# Discover Linux distribution
# try redhat type
[ -f /etc/redhat-release ] && _DISTRO=$(cat /etc/redhat-release 2>/dev/null | cut  -d" " -f1) 
# if not assuming ubuntu type
[ -f /etc/redhat-release ] || _DISTRO=$(lsb_release -is  2>/dev/null)            
if [ "$_DISTRO" == "Ubuntu" ]
then
    _RELEASE=$(lsb_release -rs)
    if [[ ${_RELEASE%%.*} != 14 ]] && [[ ${_RELEASE%%.*} != 16 ]]
    then
        [[ -z $QUIET_MODE ]] &&
            ! ask_user "WARNING! Not tested Ubuntu version. Continue assuming a trusty (14.XX)' (y/N)? " n &&
            echo "Cancelled" && exit 1
        _RELEASE = 14
    fi
elif [ "$_DISTRO" == "CentOS" ]
then
    _RELEASE="7" 
    if ! cat /etc/redhat-release | grep -q "7."
    then
        [[ -z $QUIET_MODE ]] &&
            ! ask_user "WARNING! Not tested CentOS version. Continue assuming a '$_RELEASE' type (y/N)? " n &&
            echo "Cancelled" && exit 1
    fi
elif [ "$_DISTRO" == "Red" ]
then
    _RELEASE="7" 
    if ! cat /etc/redhat-release | grep -q "7."
    then
        [[ -z $QUIET_MODE ]] &&
            ! ask_user "WARNING! Not tested Red Hat OS version. Continue assuming a '$_RELEASE' type (y/N)? " n &&
            echo "Cancelled" && exit 1
    fi
else  #[ "$_DISTRO" != "Ubuntu" -a "$_DISTRO" != "CentOS" -a "$_DISTRO" != "Red" ] 
    _DISTRO_DISCOVER=$_DISTRO
    [ -x /usr/bin/apt-get ] && _DISTRO="Ubuntu" && _RELEASE="14"
    [ -x /usr/bin/yum ]     && _DISTRO="CentOS" && _RELEASE="7"
    [[ -z $QUIET_MODE ]] &&
        ! ask_user "WARNING! Not tested Linux distribution '$_DISTRO_DISCOVER '. Continue assuming a '$_DISTRO $_RELEASE' type (y/N)? " n &&
        echo "Cancelled" && exit 1
fi

#check if installed as a service
INSTALL_AS_A_SERVICE=""
[[ "$_DISTRO" == "Ubuntu" ]] &&  [[ ${_RELEASE%%.*} == 16 ]] && [[ -z $DEVELOP ]] && INSTALL_AS_A_SERVICE="y"

# Next operations require knowing BASEFOLDER
if [[ -z "$NOCLONE" ]]; then
    if [[ -n "$INSTALL_AS_A_SERVICE" ]] ; then
        BASEFOLDER=__openmano__${RANDOM}
    else
        BASEFOLDER="${PWD}/openmano"
    fi
    [[ -n "$FORCE" ]] && rm -rf $BASEFOLDER #make idempotent
else
    HERE=$(dirname $(readlink -f ${BASH_SOURCE[0]}))
    BASEFOLDER=$(dirname $HERE)
fi

if [[ -z "$NO_PACKAGES" ]]
then
    echo -e "\n"\
        "#################################################################\n"\
        "#####        UPDATE REPOSITORIES                            #####\n"\
        "#################################################################"
    [ "$_DISTRO" == "Ubuntu" ] && apt-get update -y &&
        add-apt-repository -y cloud-archive:ocata && apt-get update -y

    [ "$_DISTRO" == "CentOS" -o "$_DISTRO" == "Red" ] && yum check-update -y
    [ "$_DISTRO" == "CentOS" ] && yum install -y epel-release
    [ "$_DISTRO" == "Red" ] && wget http://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-5.noarch.rpm \
        && rpm -ivh epel-release-7-5.noarch.rpm && yum install -y epel-release && rm -f epel-release-7-5.noarch.rpm
    [ "$_DISTRO" == "CentOS" -o "$_DISTRO" == "Red" ] && yum repolist

    echo -e "\n"\
        "#################################################################\n"\
        "#####        INSTALL REQUIRED PACKAGES                      #####\n"\
        "#################################################################"
    [ "$_DISTRO" == "Ubuntu" ] && install_packages "git make screen wget mysql-client"
    [ "$_DISTRO" == "CentOS" -o "$_DISTRO" == "Red" ] && install_packages "git make screen wget mariadb-client"

    echo -e "\n"\
        "#################################################################\n"\
        "#####        INSTALL PYTHON PACKAGES                        #####\n"\
        "#################################################################"
    [ "$_DISTRO" == "Ubuntu" ] && install_packages "python-yaml python-bottle python-mysqldb python-jsonschema "\
        "python-paramiko python-argcomplete python-requests python-logutils libxml2-dev libxslt-dev python-dev "\
        "python-pip python-crypto"
    [ "$_DISTRO" == "CentOS" -o "$_DISTRO" == "Red" ] && install_packages "PyYAML MySQL-python python-jsonschema "\
        "python-paramiko python-argcomplete python-requests python-logutils libxslt-devel libxml2-devel python-devel "\
        "python-pip python-crypto"
    # The only way to install python-bottle on Centos7 is with easy_install or pip
    [ "$_DISTRO" == "CentOS" -o "$_DISTRO" == "Red" ] && easy_install -U bottle

    # required for vmware connector TODO move that to separete opt in install script
    pip install --upgrade pip || exit 1
    pip install pyvcloud==19.1.1 || exit 1
    pip install progressbar || exit 1
    pip install prettytable || exit 1
    pip install pyvmomi || exit 1

    # required for OpenNebula connector
    pip install untangle || exit 1
    pip install -e git+https://github.com/python-oca/python-oca#egg=oca || exit 1

    # required for AWS connector
    [ "$_DISTRO" == "Ubuntu" ] && install_packages "python-boto"
    [ "$_DISTRO" == "CentOS" -o "$_DISTRO" == "Red" ] && install_packages "python-boto"  #TODO check if at Centos it exists with this name, or PIP should be used

    # install openstack client needed for using openstack as a VIM
    [ "$_DISTRO" == "Ubuntu" ] && install_packages "python-novaclient python-keystoneclient python-glanceclient "\
                                                   "python-neutronclient python-cinderclient python-openstackclient"
    [ "$_DISTRO" == "CentOS" -o "$_DISTRO" == "Red" ] && install_packages "python-devel" && easy_install \
        python-novaclient python-keystoneclient python-glanceclient python-neutronclient python-cinderclient \
        python-openstackclient #TODO revise if gcc python-pip is needed
fi  # [[ -z "$NO_PACKAGES" ]]

if [[ -z $NOCLONE ]]; then
    echo -e "\n"\
        "#################################################################\n"\
        "#####        DOWNLOAD SOURCE                                #####\n"\
        "#################################################################"
    if [[ -d "${BASEFOLDER}" ]] ; then
        if [[ -n "$FORCE" ]] ; then
            echo "deleting '${BASEFOLDER}' folder"
            rm -rf "$BASEFOLDER" #make idempotent
        elif [[ -z "$QUIET_MODE" ]] ; then
            ! ask_user "folder '${BASEFOLDER}' exists, overwrite (y/N)? " n && echo "Cancelled!" && exit 1
            rm -rf "$BASEFOLDER"
        else
            echo "'${BASEFOLDER}' folder exists. Use "--force" to overwrite" >&2 && exit 1
        fi
    fi
    su $SUDO_USER -c "git clone ${GIT_URL} ${BASEFOLDER}" || ! echo "Error cannot clone from '$GIT_URL'" >&2 || exit 1
    if [[ -n $COMMIT_ID ]] ; then
        echo -e "Installing osm-RO from refspec: $COMMIT_ID"
        su $SUDO_USER -c "git -C ${BASEFOLDER} checkout $COMMIT_ID" ||
            ! echo "Error cannot checkout '$COMMIT_ID' from '$GIT_URL'" >&2 || exit 1
    elif [[ -z $DEVELOP ]]; then
        LATEST_STABLE_TAG=`git -C "${BASEFOLDER}" tag -l "v[0-9]*" | sort -V | tail -n1`
        echo -e "Installing osm-RO from refspec: tags/${LATEST_STABLE_TAG}"
        su $SUDO_USER -c "git -C ${BASEFOLDER} checkout tags/${LATEST_STABLE_TAG}" ||
            ! echo "Error cannot checkout 'tags/${LATEST_STABLE_TAG}' from '$GIT_URL'" >&2 || exit 1
    else
        echo -e "Installing osm-RO from refspec: master"
    fi
    su $SUDO_USER -c "cp ${BASEFOLDER}/.gitignore-common ${BASEFOLDER}/.gitignore"
fi

echo -e "\n"\
    "#################################################################\n"\
    "#####        INSTALLING OSM-IM LIBRARY                      #####\n"\
    "#################################################################"
su $SUDO_USER -c "git -C ${BASEFOLDER} clone ${GIT_OSMIM_URL} IM" ||
    ! echo "Error cannot clone from '${GIT_OSMIM_URL}'" >&2 || exit 1
if [[ -n $COMMIT_ID ]] ; then
    echo -e "Installing osm-IM from refspec: $COMMIT_ID"
    su $SUDO_USER -c "git -C ${BASEFOLDER}/IM checkout $COMMIT_ID" ||
        ! echo "Error cannot checkout '$COMMIT_ID' from '${GIT_OSMIM_URL}'" >&2 || exit 1
elif [[ -z $DEVELOP ]]; then
    LATEST_STABLE_TAG=`git -C "${BASEFOLDER}/IM" tag -l "v[0-9]*" | sort -V | tail -n1`
    echo -e "Installing osm-IM from refspec: tags/${LATEST_STABLE_TAG}"
    su $SUDO_USER -c "git -C ${BASEFOLDER}/IM checkout tags/${LATEST_STABLE_TAG}" ||
        ! echo "Error cannot checkout 'tags/${LATEST_STABLE_TAG}' from '${GIT_OSMIM_URL}'" >&2 || exit 1
else
    echo -e "Installing osm-IM from refspec: master"
fi

# Install debian dependencies before setup.py
if [[ -z "$NO_PACKAGES" ]]
then
    [ "$_DISTRO" == "Ubuntu" ] && install_packages "tox debhelper python-bitarray python-lxml python-six"
    # TODO check packages for CentOS and RedHat
    [ "$_DISTRO" == "CentOS" -o "$_DISTRO" == "Red" ] && install_packages "tox debhelper python-bitarray python-lxml python-six"
    pip install --upgrade stdeb pyangbind || exit 1
fi
su $SUDO_USER -c "make -C ${BASEFOLDER}/IM all"
dpkg -i ${BASEFOLDER}/IM/deb_dist/python-osm-im*.deb ${BASEFOLDER}/IM/pyangbind/deb_dist/*.deb \
        ${BASEFOLDER}/IM/pyang/deb_dist/*.deb
rm -rf "${BASEFOLDER}/IM"
OSM_IM_PATH=`python -c 'import osm_im; print osm_im.__path__[0]'` ||
    ! echo "ERROR installing python-osm-im library!!!" >&2  || exit 1


echo -e "\n"\
    "#################################################################\n"\
    "#####        INSTALLING OVIM LIBRARY                        #####\n"\
    "#################################################################"
su $SUDO_USER -c "git -C ${BASEFOLDER} clone ${GIT_OVIM_URL} openvim" ||
    ! echo "Error cannot clone from '${GIT_OVIM_URL}'" || exit 1
if [[ -n $COMMIT_ID ]] ; then
    echo -e "Installing lib_osm_openvim from refspec: $COMMIT_ID"
    su $SUDO_USER -c "git -C ${BASEFOLDER}/openvim checkout $COMMIT_ID" ||
        ! echo "Error cannot checkout '$COMMIT_ID' from '${GIT_OVIM_URL}'" || exit 1
elif [[ -z $DEVELOP ]]; then
    LATEST_STABLE_TAG=`git -C "${BASEFOLDER}/openvim" tag -l "v[0-9]*" | sort -V | tail -n1`
    echo -e "Installing lib_osm_openvim from refspec: tags/${LATEST_STABLE_TAG}"
    su $SUDO_USER -c "git -C ${BASEFOLDER}/openvim checkout tags/${LATEST_STABLE_TAG}" ||
        ! echo "Error cannot checkout 'tags/${LATEST_STABLE_TAG}' from '${GIT_OVIM_URL}'" || exit 1
else
    echo -e "Installing lib_osm_openvim from refspec: master"
fi

# Install debian dependencies before setup.py
if [[ -z "$NO_PACKAGES" ]]
then
    [ "$_DISTRO" == "Ubuntu" ] && install_packages \
        "libmysqlclient-dev python-cffi python-packaging python-pkgconfig python-pycparser libssl-dev libffi-dev"
    # TODO check if that is the name in CentOS and RedHat
    [ "$_DISTRO" == "CentOS" -o "$_DISTRO" == "Red" ] && install_packages \
        "libmysqlclient-dev python-cffi python-packaging python-pkgconfig python-pycparser libssl-dev libffi-dev"
    pip install --upgrade stdeb setuptools-version-command || exit 1
fi
su $SUDO_USER -c "make -C ${BASEFOLDER}/openvim lite"
dpkg -i ${BASEFOLDER}/openvim/.build/python-lib-osm-openvim*.deb
rm -rf "${BASEFOLDER}/openvim"
OSMLIBOVIM_PATH=`python -c 'import lib_osm_openvim; print lib_osm_openvim.__path__[0]'` ||
    ! echo "ERROR installing python-lib-osm-openvim library!!!" >&2  || exit 1

if [ "$_DISTRO" == "CentOS" -o "$_DISTRO" == "Red" ]
then
    echo -e "\n"\
        "#################################################################\n"\
        "#####        CONFIGURE firewalld                            #####\n"\
        "#################################################################"
    if [[ -z $QUIET_MODE ]] || ask_user "Configure firewalld for openmanod port 9090 (Y/n)? " y
    then
        #Creates a service file for openmano
        echo '<?xml version="1.0" encoding="utf-8"?>
<service>
 <short>openmanod</short>
 <description>openmanod service</description>
 <port protocol="tcp" port="9090"/>
</service>' > /etc/firewalld/services/openmanod.xml
        #put proper permissions
        pushd /etc/firewalld/services > /dev/null
        restorecon openmanod.xml
        chmod 640 openmanod.xml
        popd > /dev/null
        #Add the openmanod service to the default zone permanently and reload the firewall configuration
        firewall-cmd --permanent --add-service=openmanod > /dev/null
        firewall-cmd --reload > /dev/null
        echo "done." 
    else
        echo "skipping."
    fi
fi

echo -e "\n"\
    "#################################################################\n"\
    "#####        CONFIGURE OPENMANO CLIENT                      #####\n"\
    "#################################################################"
#creates a link at ~/bin if not configured as a service
if [[ -z "$INSTALL_AS_A_SERVICE" ]]
then
    su $SUDO_USER -c 'mkdir -p ${HOME}/bin'
    su $SUDO_USER -c 'rm -f ${HOME}/bin/openmano'
    su $SUDO_USER -c 'rm -f ${HOME}/bin/openmano-report'
    su $SUDO_USER -c 'rm -f ${HOME}/bin/service-openmano'
    su $SUDO_USER -c "ln -s '${BASEFOLDER}/openmano' "'${HOME}/bin/openmano'
    su $SUDO_USER -c "ln -s '${BASEFOLDER}/scripts/openmano-report.sh'   "'${HOME}/bin/openmano-report'
    su $SUDO_USER -c "ln -s '${BASEFOLDER}/scripts/service-openmano'  "'${HOME}/bin/service-openmano'

    #insert /home/<user>/bin in the PATH
    #skiped because normally this is done authomatically when ~/bin exists
    #if ! su $SUDO_USER -c 'echo $PATH' | grep -q "${HOME}/bin"
    #then
    #    echo "    inserting /home/$SUDO_USER/bin in the PATH at .bashrc"
    #    su $SUDO_USER -c 'echo "PATH=\$PATH:\${HOME}/bin" >> ~/.bashrc'
    #fi
    
    if [[ $SUDO_USER == root ]]
    then
        if ! echo $PATH | grep -q "${HOME}/bin"
        then
            echo "PATH=\$PATH:\${HOME}/bin" >> ${HOME}/.bashrc
        fi
    fi
fi

#configure arg-autocomplete for this user
#in case of minimal instalation this package is not installed by default
[[ "$_DISTRO" == "CentOS" || "$_DISTRO" == "Red" ]] && yum install -y bash-completion
#su $SUDO_USER -c 'mkdir -p ~/.bash_completion.d'
su $SUDO_USER -c 'activate-global-python-argcomplete --user'
if ! su  $SUDO_USER -c 'grep -q bash_completion.d/python-argcomplete.sh ${HOME}/.bashrc'
then
    echo "    inserting .bash_completion.d/python-argcomplete.sh execution at .bashrc"
    su $SUDO_USER -c 'echo ". ${HOME}/.bash_completion.d/python-argcomplete.sh" >> ~/.bashrc'
fi

if [ -z "$NO_DB" ]; then
    echo -e "\n"\
        "#################################################################\n"\
        "#####               INSTALL DATABASE SERVER                 #####\n"\
        "#################################################################"

    if [ -n "$QUIET_MODE" ]; then
        DB_QUIET='-q'
    fi
    ${BASEFOLDER}/database_utils/install-db-server.sh -U $DBUSER ${DBPASSWD_PARAM/p/P} $DB_QUIET $DB_FORCE_UPDATE || exit 1
    echo -e "\n"\
        "#################################################################\n"\
        "#####        CREATE AND INIT MANO_VIM DATABASE              #####\n"\
        "#################################################################"
    # Install mano_vim_db after setup
    ${OSMLIBOVIM_PATH}/database_utils/install-db-server.sh -U $DBUSER ${DBPASSWD_PARAM/p/P} -u mano -p manopw -d mano_vim_db --no-install-packages $DB_QUIET $DB_FORCE_UPDATE || exit 1
fi   # [ -z "$NO_DB" ]

if [[ -n "$INSTALL_AS_A_SERVICE"  ]]
then
    echo -e "\n"\
        "#################################################################\n"\
        "#####        CONFIGURE OPENMANO SERVICE                     #####\n"\
        "#################################################################"

    ${BASEFOLDER}/scripts/install-openmano-service.sh -f ${BASEFOLDER} `[[ -z "$NOCLONE" ]] && echo "-d"`
    # rm -rf ${BASEFOLDER}
    # alias service-openmano="service openmano"
    # echo 'alias service-openmano="service openmano"' >> ${HOME}/.bashrc
    echo
    echo "Done!  installed at /opt/openmano"
    echo " Manage server with 'sudo -E service osm-ro start|stop|status|...' "
else
    echo
    echo "Done!  you may need to logout and login again for loading client configuration"
    echo " Run './${BASEFOLDER}/scripts/service-openmano start' for starting openmano in a screen"
fi
