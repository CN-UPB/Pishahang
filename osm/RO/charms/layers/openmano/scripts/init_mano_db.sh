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

DBUSER="mano"
DBPASS=""
DBHOST="localhost"
DBPORT="3306"
DBNAME="mano_db"
CREATEDB=""

# Detect paths
MYSQL=$(which mysql)
AWK=$(which awk)
GREP=$(which grep)
#DIRNAME=`dirname $0`
DIRNAME=/opt/openmano/database_utils

function usage(){
    echo -e "Usage: $0 OPTIONS"
    echo -e "  Inits openmano database; deletes previous one and loads from ${DBNAME}_structure.sql"
    echo -e "  OPTIONS"
    echo -e "     -u USER  database user. '$DBUSER' by default. Prompts if DB access fails"
    echo -e "     -p PASS  database password. 'No password' by default. Prompts if DB access fails"
    echo -e "     -P PORT  database port. '$DBPORT' by default"
    echo -e "     -h HOST  database host. '$DBHOST' by default"
    echo -e "     -d NAME  database name. '$DBNAME' by default.  Prompts if DB access fails"
    echo -e "     --help   shows this help"
    echo -e "     --createdb   forces the deletion and creation of the database"
}

while getopts ":u:p:P:d:h:-:" o; do
    case "${o}" in
        u)
            DBUSER="$OPTARG"
            ;;
        p)
            DBPASS="$OPTARG"
            ;;
        P)
            DBPORT="$OPTARG"
            ;;
        d)
            DBNAME="$OPTARG"
            ;;
        h)
            DBHOST="$OPTARG"
            ;;
        -)
            if [ "${OPTARG}" == "help" ]; then
                usage && exit 0
            elif [ "${OPTARG}" == "createdb" ]; then
                CREATEDB="yes"
            else
                echo "Invalid option: --$OPTARG" >&2 && usage  >&2
                exit 1
            fi
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2 && usage  >&2
            exit 1
            ;;
        :)
            echo "Option -$OPTARG requires an argument." >&2 && usage  >&2
            exit 1
            ;;
        *)
            usage >&2
            exit -1
            ;;
    esac
done
shift $((OPTIND-1))

#check and ask for database user password
DBUSER_="-u$DBUSER"
DBPASS_=""
[ -n "$DBPASS" ] && DBPASS_="-p$DBPASS"
DBHOST_="-h$DBHOST"
DBPORT_="-P$DBPORT"

TEMPFILE="$(mktemp -q --tmpdir "initmanodb.XXXXXX")"
trap 'rm -f "$TEMPFILE"' EXIT SIGINT SIGTERM
chmod 0600 "$TEMPFILE"
cat >"$TEMPFILE" <<EOF
[client]
user="${DBUSER}"
password="${DBPASS}"
EOF
DEF_EXTRA_FILE_PARAM="--defaults-extra-file=$TEMPFILE"

while !  mysql $DEF_EXTRA_FILE_PARAM $DBHOST_ $DBPORT_ -e "quit" >/dev/null 2>&1
do
        [ -n "$logintry" ] &&  echo -e "\nInvalid database credentials!!!. Try again (Ctrl+c to abort)"
        [ -z "$logintry" ] &&  echo -e "\nProvide database credentials"
#        read -e -p "mysql database name($DBNAME): " KK
#        [ -n "$KK" ] && DBNAME="$KK"
        read -e -p "mysql user($DBUSER): " KK
        [ -n "$KK" ] && DBUSER="$KK"
        read -e -s -p "mysql password: " DBPASS
        cat >"$TEMPFILE" <<EOF
[client]
user="${DBUSER}"
password="${DBPASS}"
EOF
        logintry="yes"
        echo
done

if [ -n "${CREATEDB}" ]; then
    echo "    deleting previous database ${DBNAME}"
    echo "DROP DATABASE IF EXISTS ${DBNAME}" | mysql $DEF_EXTRA_FILE_PARAM $DBHOST_ $DBPORT_
    echo "    creating database ${DBNAME}"
    mysqladmin $DEF_EXTRA_FILE_PARAM  $DBHOST_ $DBPORT_ -s create ${DBNAME} || exit 1
fi

echo "    loading ${DIRNAME}/${DBNAME}_structure.sql"
#echo 'mysql '$DEF_EXTRA_FILE_PARAM' '$DBHOST_' '$DBPORT_' '$DBNAME' < '${DIRNAME}'/mano_db_structure.sql'
mysql $DEF_EXTRA_FILE_PARAM $DBHOST_ $DBPORT_ $DBNAME < ${DIRNAME}/mano_db_structure.sql

echo "    migrage database version"
${DIRNAME}/migrate_mano_db.sh $DBHOST_ $DBPORT_ $DBUSER_ $DBPASS_ -d$DBNAME

