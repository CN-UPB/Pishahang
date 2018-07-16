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
DEFAULT_DBPASS="manopw"
DBHOST=""
DBPORT="3306"
DBNAME="mano_db"
QUIET_MODE=""
CREATEDB=""

# Detect paths
MYSQL=$(which mysql)
AWK=$(which awk)
GREP=$(which grep)
DIRNAME=`dirname $(readlink -f $0)`

function usage(){
    echo -e "Usage: $0 OPTIONS [version]"
    echo -e "  Inits openmano database; deletes previous one and loads from ${DBNAME}_structure.sql"\
    echo -e "   and data from host_ranking.sql, nets.sql, of_ports_pci_correspondece*.sql"
            "If [version]  is not provided, it is upgraded to the last version"
    echo -e "  OPTIONS"
    echo -e "     -u USER  database user. '$DBUSER' by default. Prompts if DB access fails"
    echo -e "     -p PASS  database password. If missing it tries without and '$DEFAULT_DBPASS' password before prompting"
    echo -e "     -P PORT  database port. '$DBPORT' by default"
    echo -e "     -h HOST  database host. 'localhost' by default"
    echo -e "     -d NAME  database name. '$DBNAME' by default.  Prompts if DB access fails"
    echo -e "     -q --quiet: Do not prompt for credentials and exit if cannot access to database"
    echo -e "     --createdb   forces the deletion and creation of the database"
    echo -e "     --help   shows this help"
}

while getopts ":u:p:P:h:d:q-:" o; do
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
        q)
            export QUIET_MODE="-q"
            ;;
        -)
            [ "${OPTARG}" == "help" ] && usage && exit 0
            [ "${OPTARG}" == "quiet" ] && export QUIET_MODE="-q" && continue
            [ "${OPTARG}" == "createdb" ] && export CREATEDB=yes && continue
            echo "Invalid option: '--$OPTARG'. Type --help for more information" >&2
            exit 1
            ;;
        \?)
            echo "Invalid option: '-$OPTARG'. Type --help for more information" >&2
            exit 1
            ;;
        :)
            echo "Option '-$OPTARG' requires an argument. Type --help for more information" >&2
            exit 1
            ;;
        *)
            usage >&2
            exit 1
            ;;
    esac
done
shift $((OPTIND-1))

DB_VERSION=$1

if [ -n "$DB_VERSION" ] ; then
    # check it is a number and an allowed one
    [ "$DB_VERSION" -eq "$DB_VERSION" ] 2>/dev/null || 
        ! echo "parameter 'version' requires a integer value" >&2 || exit 1
fi

# Creating temporary file
TEMPFILE="$(mktemp -q --tmpdir "initdb.XXXXXX")"
trap 'rm -f "$TEMPFILE"' EXIT
chmod 0600 "$TEMPFILE"
DEF_EXTRA_FILE_PARAM="--defaults-extra-file=$TEMPFILE"
echo -e "[client]\n user='${DBUSER}'\n password='$DBPASS'\n host='$DBHOST'\n port='$DBPORT'" > "$TEMPFILE"

if [ -n "${CREATEDB}" ] ; then
    FIRST_TRY="yes"
    while ! DB_ERROR=`mysqladmin "$DEF_EXTRA_FILE_PARAM" -s status 2>&1 >/dev/null` ; do
        # if password is not provided, try silently with $DEFAULT_DBPASS before exit or prompt for credentials
        [[ -n "$FIRST_TRY" ]] && [[ -z "$DBPASS" ]] && DBPASS="$DEFAULT_DBPASS" &&
            echo -e "[client]\n user='${DBUSER}'\n password='$DBPASS'\n host='$DBHOST'\n port='$DBPORT'" > "$TEMPFILE" &&
            continue
        echo "$DB_ERROR"
        [[ -n "$QUIET_MODE" ]] && echo -e "Invalid admin database credentials!!!" >&2 && exit 1
        echo -e "Provide database credentials (Ctrl+c to abort):"
        read -e -p "    mysql user($DBUSER): " KK
        [ -n "$KK" ] && DBUSER="$KK"
        read -e -s -p "    mysql password: " DBPASS
        echo -e "[client]\n user='${DBUSER}'\n password='$DBPASS'\n host='$DBHOST'\n port='$DBPORT'" > "$TEMPFILE"
        FIRST_TRY=""
        echo
    done
    # echo "    deleting previous database ${DBNAME} if it exists"
    mysqladmin $DEF_EXTRA_FILE_PARAM DROP "${DBNAME}" -f && echo "Previous database deleted"
    echo "    creating database ${DBNAME}"
    mysqladmin $DEF_EXTRA_FILE_PARAM create "${DBNAME}" || exit 1
fi

# Check and ask for database user password
FIRST_TRY="yes"
while ! DB_ERROR=`mysql "$DEF_EXTRA_FILE_PARAM" $DBNAME -e "quit" 2>&1 >/dev/null`
do
    # if password is not provided, try silently with $DEFAULT_DBPASS before exit or prompt for credentials
    [[ -n "$FIRST_TRY" ]] && [[ -z "$DBPASS" ]] && DBPASS="$DEFAULT_DBPASS" &&
        echo -e "[client]\n user='${DBUSER}'\n password='$DBPASS'\n host='$DBHOST'\n port='$DBPORT'" > "$TEMPFILE" &&
        continue
    echo "$DB_ERROR"
    [[ -n "$QUIET_MODE" ]] && echo -e "Invalid database credentials!!!" >&2 && exit 1
    echo -e "Provide database name and credentials (Ctrl+c to abort):"
    read -e -p "    mysql database name($DBNAME): " KK
    [ -n "$KK" ] && DBNAME="$KK"
    read -e -p "    mysql user($DBUSER): " KK
    [ -n "$KK" ] && DBUSER="$KK"
    read -e -s -p "    mysql password: " DBPASS
    echo -e "[client]\n user='${DBUSER}'\n password='$DBPASS'\n host='$DBHOST'\n port='$DBPORT'" > "$TEMPFILE"
    FIRST_TRY=""
    echo
done

DBCMD="mysql $DEF_EXTRA_FILE_PARAM $DBNAME"
DBUSER_="" && [ -n "$DBUSER" ] && DBUSER_="-u$DBUSER"
DBPASS_="" && [ -n "$DBPASS" ] && DBPASS_="-p$DBPASS"
DBHOST_="" && [ -n "$DBHOST" ] && DBHOST_="-h$DBHOST"
DBPORT_="-P$DBPORT"

echo "    loading ${DIRNAME}/mano_db_structure.sql"
sed -e "s/{{mano_db}}/$DBNAME/" ${DIRNAME}/mano_db_structure.sql |  mysql $DEF_EXTRA_FILE_PARAM

echo "    migrage database version"
# echo "${DIRNAME}/migrate_mano_db.sh $DBHOST_ $DBPORT_ $DBUSER_ $DBPASS_ -d$DBNAME $QUIET_MODE $DB_VERSION"
${DIRNAME}/migrate_mano_db.sh $DBHOST_ $DBPORT_ $DBUSER_ $DBPASS_ -d$DBNAME $QUIET_MODE $DB_VERSION

