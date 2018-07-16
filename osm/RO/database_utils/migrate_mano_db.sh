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

#
#Upgrade/Downgrade openmano database preserving the content
#

DBUSER="mano"
DBPASS=""
DEFAULT_DBPASS="manopw"
DBHOST=""
DBPORT="3306"
DBNAME="mano_db"
QUIET_MODE=""
#TODO update it with the last database version
LAST_DB_VERSION=29

# Detect paths
MYSQL=$(which mysql)
AWK=$(which awk)
GREP=$(which grep)

function usage(){
    echo -e "Usage: $0 OPTIONS [version]"
    echo -e "  Upgrades/Downgrades openmano database preserving the content."\
            "If [version]  is not provided, it is upgraded to the last version"
    echo -e "  OPTIONS"
    echo -e "     -u USER  database user. '$DBUSER' by default. Prompts if DB access fails"
    echo -e "     -p PASS  database password. If missing it tries without and '$DEFAULT_DBPASS' password before prompting"
    echo -e "     -P PORT  database port. '$DBPORT' by default"
    echo -e "     -h HOST  database host. 'localhost' by default"
    echo -e "     -d NAME  database name. '$DBNAME' by default.  Prompts if DB access fails"
    echo -e "     -q --quiet: Do not prompt for credentials and exit if cannot access to database"
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
            export QUIET_MODE=yes
            ;;
        -)
            [ "${OPTARG}" == "help" ] && usage && exit 0
            [ "${OPTARG}" == "quiet" ] && export QUIET_MODE=yes && continue
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
    if [ "$DB_VERSION" -lt 0 ] || [ "$DB_VERSION" -gt "$LAST_DB_VERSION" ] ; then
        echo "parameter 'version' requires a valid database version between '0' and '$LAST_DB_VERSION'"\
             "If you need an upper version, get a newer version of this script '$0'" >&2
        exit 1
    fi
else
    DB_VERSION="$LAST_DB_VERSION"
fi

# Creating temporary file
TEMPFILE="$(mktemp -q --tmpdir "migratemanodb.XXXXXX")"
trap 'rm -f "$TEMPFILE"' EXIT
chmod 0600 "$TEMPFILE"
DEF_EXTRA_FILE_PARAM="--defaults-extra-file=$TEMPFILE"
echo -e "[client]\n user='${DBUSER}'\n password='$DBPASS'\n host='$DBHOST'\n port='$DBPORT'" > "$TEMPFILE"

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
#echo DBCMD $DBCMD

#GET DATABASE VERSION
#check that the database seems a openmano database
if ! echo -e "show create table vnfs;\nshow create table scenarios" | $DBCMD >/dev/null 2>&1
then
    echo "    database $DBNAME does not seem to be an openmano database" >&2
    exit 1;
fi

if ! echo 'show create table schema_version;' | $DBCMD >/dev/null 2>&1
then
    DATABASE_VER="0.0"
    DATABASE_VER_NUM=0
else
    DATABASE_VER_NUM=`echo "select max(version_int) from schema_version;" | $DBCMD | tail -n+2` 
    DATABASE_VER=`echo "select version from schema_version where version_int='$DATABASE_VER_NUM';" | $DBCMD | tail -n+2` 
    [ "$DATABASE_VER_NUM" -lt 0 -o "$DATABASE_VER_NUM" -gt 100 ] &&
        echo "    Error can not get database version ($DATABASE_VER?)" >&2 && exit 1
    #echo "_${DATABASE_VER_NUM}_${DATABASE_VER}"
fi

[ "$DATABASE_VER_NUM" -gt "$LAST_DB_VERSION" ] &&
    echo "Database has been upgraded with a newer version of this script. Use this version to downgrade" >&2 &&
    exit 1

#GET DATABASE TARGET VERSION
#DB_VERSION=0
#[ $OPENMANO_VER_NUM -ge 2002 ] && DB_VERSION=1   #0.2.2 =>  1
#[ $OPENMANO_VER_NUM -ge 2005 ] && DB_VERSION=2   #0.2.5 =>  2
#[ $OPENMANO_VER_NUM -ge 3003 ] && DB_VERSION=3   #0.3.3 =>  3
#[ $OPENMANO_VER_NUM -ge 3005 ] && DB_VERSION=4   #0.3.5 =>  4
#[ $OPENMANO_VER_NUM -ge 4001 ] && DB_VERSION=5   #0.4.1 =>  5
#[ $OPENMANO_VER_NUM -ge 4002 ] && DB_VERSION=6   #0.4.2 =>  6
#[ $OPENMANO_VER_NUM -ge 4003 ] && DB_VERSION=7   #0.4.3 =>  7
#[ $OPENMANO_VER_NUM -ge 4032 ] && DB_VERSION=8   #0.4.32=>  8
#[ $OPENMANO_VER_NUM -ge 4033 ] && DB_VERSION=9   #0.4.33=>  9
#[ $OPENMANO_VER_NUM -ge 4036 ] && DB_VERSION=10  #0.4.36=>  10
#[ $OPENMANO_VER_NUM -ge 4043 ] && DB_VERSION=11  #0.4.43=>  11
#[ $OPENMANO_VER_NUM -ge 4046 ] && DB_VERSION=12  #0.4.46=>  12
#[ $OPENMANO_VER_NUM -ge 4047 ] && DB_VERSION=13  #0.4.47=>  13
#[ $OPENMANO_VER_NUM -ge 4057 ] && DB_VERSION=14  #0.4.57=>  14
#[ $OPENMANO_VER_NUM -ge 4059 ] && DB_VERSION=15  #0.4.59=>  15
#[ $OPENMANO_VER_NUM -ge 5002 ] && DB_VERSION=16  #0.5.2 =>  16
#[ $OPENMANO_VER_NUM -ge 5003 ] && DB_VERSION=17  #0.5.3 =>  17
#[ $OPENMANO_VER_NUM -ge 5004 ] && DB_VERSION=18  #0.5.4 =>  18
#[ $OPENMANO_VER_NUM -ge 5005 ] && DB_VERSION=19  #0.5.5 =>  19
#[ $OPENMANO_VER_NUM -ge 5009 ] && DB_VERSION=20  #0.5.9 =>  20
#[ $OPENMANO_VER_NUM -ge 5015 ] && DB_VERSION=21  #0.5.15 =>  21
#[ $OPENMANO_VER_NUM -ge 5016 ] && DB_VERSION=22  #0.5.16 =>  22
#[ $OPENMANO_VER_NUM -ge 5020 ] && DB_VERSION=23  #0.5.20 =>  23
#[ $OPENMANO_VER_NUM -ge 5021 ] && DB_VERSION=24  #0.5.21 =>  24
#[ $OPENMANO_VER_NUM -ge 5022 ] && DB_VERSION=25  #0.5.22 =>  25
#[ $OPENMANO_VER_NUM -ge 5024 ] && DB_VERSION=26  #0.5.24 =>  26
#[ $OPENMANO_VER_NUM -ge 5025 ] && DB_VERSION=27  #0.5.25 =>  27
#[ $OPENMANO_VER_NUM -ge 5052 ] && DB_VERSION=28  #0.5.52 =>  28
#[ $OPENMANO_VER_NUM -ge 5059 ] && DB_VERSION=28  #0.5.59 =>  29
#TODO ... put next versions here

function upgrade_to_1(){
    # echo "    upgrade database from version 0.0 to version 0.1"
    echo "      CREATE TABLE \`schema_version\`"
    sql "CREATE TABLE \`schema_version\` (
	\`version_int\` INT NOT NULL COMMENT 'version as a number. Must not contain gaps',
	\`version\` VARCHAR(20) NOT NULL COMMENT 'version as a text',
	\`openmano_ver\` VARCHAR(20) NOT NULL COMMENT 'openmano version',
	\`comments\` VARCHAR(2000) NULL COMMENT 'changes to database',
	\`date\` DATE NULL,
	PRIMARY KEY (\`version_int\`)
	)
	COMMENT='database schema control version'
	COLLATE='utf8_general_ci'
	ENGINE=InnoDB;"
    sql "INSERT INTO \`schema_version\` (\`version_int\`, \`version\`, \`openmano_ver\`, \`comments\`, \`date\`)
	 VALUES (1, '0.1', '0.2.2', 'insert schema_version', '2015-05-08');"
}
function downgrade_from_1(){
    # echo "    downgrade database from version 0.1 to version 0.0"
    echo "      DROP TABLE \`schema_version\`"
    sql "DROP TABLE \`schema_version\`;"
}
function upgrade_to_2(){
    # echo "    upgrade database from version 0.1 to version 0.2"
    echo "      Add columns user/passwd to table 'vim_tenants'"
    sql "ALTER TABLE vim_tenants ADD COLUMN user VARCHAR(36) NULL COMMENT 'Credentials for vim' AFTER created,
	ADD COLUMN passwd VARCHAR(50) NULL COMMENT 'Credentials for vim' AFTER user;"
    echo "      Add table 'images' and 'datacenters_images'"
    sql "CREATE TABLE images (
	uuid VARCHAR(36) NOT NULL,
	name VARCHAR(50) NOT NULL,
	location VARCHAR(200) NOT NULL,
	description VARCHAR(100) NULL,
	metadata VARCHAR(400) NULL,
	PRIMARY KEY (uuid),
	UNIQUE INDEX location (location)  )
        COLLATE='utf8_general_ci'
        ENGINE=InnoDB;"
    sql "CREATE TABLE datacenters_images (
	id INT NOT NULL AUTO_INCREMENT,
	image_id VARCHAR(36) NOT NULL,
	datacenter_id VARCHAR(36) NOT NULL,
	vim_id VARCHAR(36) NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT FK__images FOREIGN KEY (image_id) REFERENCES images (uuid) ON UPDATE CASCADE ON DELETE CASCADE,
	CONSTRAINT FK__datacenters_i FOREIGN KEY (datacenter_id) REFERENCES datacenters (uuid) ON UPDATE CASCADE ON DELETE CASCADE  )
        COLLATE='utf8_general_ci'
        ENGINE=InnoDB;"
    echo "      migrate data from table 'vms' into 'images'"
    sql "INSERT INTO images (uuid, name, location) SELECT DISTINCT vim_image_id, vim_image_id, image_path FROM vms;"
    sql "INSERT INTO datacenters_images (image_id, datacenter_id, vim_id)
          SELECT DISTINCT vim_image_id, datacenters.uuid, vim_image_id FROM vms JOIN datacenters;"
    echo "      Add table 'flavors' and 'datacenter_flavors'"
    sql "CREATE TABLE flavors (
	uuid VARCHAR(36) NOT NULL,
	name VARCHAR(50) NOT NULL,
	description VARCHAR(100) NULL,
	disk SMALLINT(5) UNSIGNED NULL DEFAULT NULL,
	ram SMALLINT(5) UNSIGNED NULL DEFAULT NULL,
	vcpus SMALLINT(5) UNSIGNED NULL DEFAULT NULL,
	extended VARCHAR(2000) NULL DEFAULT NULL COMMENT 'Extra description json format of needed resources and pining, orginized in sets per numa',
	PRIMARY KEY (uuid)  )
        COLLATE='utf8_general_ci'
        ENGINE=InnoDB;"
    sql "CREATE TABLE datacenters_flavors (
	id INT NOT NULL AUTO_INCREMENT,
	flavor_id VARCHAR(36) NOT NULL,
	datacenter_id VARCHAR(36) NOT NULL,
	vim_id VARCHAR(36) NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT FK__flavors FOREIGN KEY (flavor_id) REFERENCES flavors (uuid) ON UPDATE CASCADE ON DELETE CASCADE,
	CONSTRAINT FK__datacenters_f FOREIGN KEY (datacenter_id) REFERENCES datacenters (uuid) ON UPDATE CASCADE ON DELETE CASCADE  )
        COLLATE='utf8_general_ci'
        ENGINE=InnoDB;"
    echo "      migrate data from table 'vms' into 'flavors'"
    sql "INSERT INTO flavors (uuid, name) SELECT DISTINCT vim_flavor_id, vim_flavor_id FROM vms;"
    sql "INSERT INTO datacenters_flavors (flavor_id, datacenter_id, vim_id)
          SELECT DISTINCT vim_flavor_id, datacenters.uuid, vim_flavor_id FROM vms JOIN datacenters;"
    sql "ALTER TABLE vms ALTER vim_flavor_id DROP DEFAULT, ALTER vim_image_id DROP DEFAULT;
          ALTER TABLE vms CHANGE COLUMN vim_flavor_id flavor_id VARCHAR(36) NOT NULL COMMENT 'Link to flavor table' AFTER vnf_id,
          CHANGE COLUMN vim_image_id image_id VARCHAR(36) NOT NULL COMMENT 'Link to image table' AFTER flavor_id, 
          ADD CONSTRAINT FK_vms_images  FOREIGN KEY (image_id) REFERENCES  images (uuid),
          ADD CONSTRAINT FK_vms_flavors FOREIGN KEY (flavor_id) REFERENCES flavors (uuid);"
    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) VALUES (2, '0.2', '0.2.5', 'new tables images,flavors', '2015-07-13');"

}   
     
function downgrade_from_2(){
    # echo "    downgrade database from version 0.2 to version 0.1"
    echo "       migrate back data from 'datacenters_images' 'datacenters_flavors' into 'vms'"
    sql "ALTER TABLE vms ALTER image_id DROP DEFAULT, ALTER flavor_id DROP DEFAULT;
          ALTER TABLE vms CHANGE COLUMN flavor_id vim_flavor_id VARCHAR(36) NOT NULL COMMENT 'Flavor ID in the VIM DB' AFTER vnf_id,
          CHANGE COLUMN image_id vim_image_id VARCHAR(36) NOT NULL COMMENT 'Image ID in the VIM DB' AFTER vim_flavor_id,
          DROP FOREIGN KEY FK_vms_flavors, DROP INDEX FK_vms_flavors,
          DROP FOREIGN KEY FK_vms_images, DROP INDEX FK_vms_images;"
#    echo "UPDATE v SET v.vim_image_id=di.vim_id
#          FROM  vms as v INNER JOIN images as i ON v.vim_image_id=i.uuid 
#          INNER JOIN datacenters_images as di ON i.uuid=di.image_id;"
    echo "      Delete columns 'user/passwd' from 'vim_tenants'"
    sql "ALTER TABLE vim_tenants DROP COLUMN user, DROP COLUMN passwd; "
    echo "        delete tables 'datacenter_images', 'images'"
    sql "DROP TABLE \`datacenters_images\`;"
    sql "DROP TABLE \`images\`;"
    echo "        delete tables 'datacenter_flavors', 'flavors'"
    sql "DROP TABLE \`datacenters_flavors\`;"
    sql "DROP TABLE \`flavors\`;"
    sql "DELETE FROM schema_version WHERE version_int='2';"
}

function upgrade_to_3(){
    # echo "    upgrade database from version 0.2 to version 0.3"
    echo "      Change table 'logs', 'uuids"
    sql "ALTER TABLE logs CHANGE COLUMN related related VARCHAR(36) NOT NULL COMMENT 'Relevant element for the log' AFTER nfvo_tenant_id;"
    sql "ALTER TABLE uuids CHANGE COLUMN used_at used_at VARCHAR(36) NULL DEFAULT NULL COMMENT 'Table that uses this UUID' AFTER created_at;"
    echo "      Add column created to table 'datacenters_images' and 'datacenters_flavors'"
    for table in datacenters_images datacenters_flavors
    do
        sql "ALTER TABLE $table ADD COLUMN created ENUM('true','false') NOT NULL DEFAULT 'false' 
            COMMENT 'Indicates if it has been created by openmano, or already existed' AFTER vim_id;"
    done
    sql "ALTER TABLE images CHANGE COLUMN metadata metadata VARCHAR(2000) NULL DEFAULT NULL AFTER description;"
    echo "      Allow null to column 'vim_interface_id' in 'instance_interfaces'"
    sql "ALTER TABLE instance_interfaces CHANGE COLUMN vim_interface_id vim_interface_id VARCHAR(36) NULL DEFAULT NULL COMMENT 'vim identity for that interface' AFTER interface_id; "
    echo "      Add column config to table 'datacenters'"
    sql "ALTER TABLE datacenters ADD COLUMN config VARCHAR(4000) NULL DEFAULT NULL COMMENT 'extra config information in json' AFTER vim_url_admin;
	"
    echo "      Add column datacenter_id to table 'vim_tenants'"
    sql "ALTER TABLE vim_tenants ADD COLUMN datacenter_id VARCHAR(36) NULL COMMENT 'Datacenter of this tenant' AFTER uuid,
	DROP INDEX name, DROP INDEX vim_tenant_id;"
    sql "ALTER TABLE vim_tenants CHANGE COLUMN name vim_tenant_name VARCHAR(36) NULL DEFAULT NULL COMMENT 'tenant name at VIM' AFTER datacenter_id,
	CHANGE COLUMN vim_tenant_id vim_tenant_id VARCHAR(36) NULL DEFAULT NULL COMMENT 'Tenant ID at VIM' AFTER vim_tenant_name;"
    echo "UPDATE vim_tenants as vt LEFT JOIN tenants_datacenters as td ON vt.uuid=td.vim_tenant_id
	SET vt.datacenter_id=td.datacenter_id;"
    sql "DELETE FROM vim_tenants WHERE datacenter_id is NULL;"
    sql "ALTER TABLE vim_tenants ALTER datacenter_id DROP DEFAULT;
	ALTER TABLE vim_tenants
	CHANGE COLUMN datacenter_id datacenter_id VARCHAR(36) NOT NULL COMMENT 'Datacenter of this tenant' AFTER uuid;"
    sql "ALTER TABLE vim_tenants ADD CONSTRAINT FK_vim_tenants_datacenters FOREIGN KEY (datacenter_id) REFERENCES datacenters (uuid)
	ON UPDATE CASCADE ON DELETE CASCADE;"

    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) VALUES (3, '0.3', '0.3.3', 'alter vim_tenant tables', '2015-07-28');"
}


function downgrade_from_3(){
    # echo "    downgrade database from version 0.3 to version 0.2"
    echo "      Change back table 'logs', 'uuids'"
    sql "ALTER TABLE logs CHANGE COLUMN related related ENUM('nfvo_tenants','datacenters','vim_tenants','tenants_datacenters','vnfs','vms','interfaces','nets','scenarios','sce_vnfs','sce_interfaces','sce_nets','instance_scenarios','instance_vnfs','instance_vms','instance_nets','instance_interfaces') NOT NULL COMMENT 'Relevant element for the log' AFTER nfvo_tenant_id;"
    sql "ALTER TABLE uuids CHANGE COLUMN used_at used_at ENUM('nfvo_tenants','datacenters','vim_tenants','vnfs','vms','interfaces','nets','scenarios','sce_vnfs','sce_interfaces','sce_nets','instance_scenarios','instance_vnfs','instance_vms','instance_nets','instance_interfaces') NULL DEFAULT NULL COMMENT 'Table that uses this UUID' AFTER created_at;"
    echo "      Delete column created from table 'datacenters_images' and 'datacenters_flavors'"
    for table in datacenters_images datacenters_flavors
    do
        sql "ALTER TABLE $table DROP COLUMN created;"
    done
    sql "ALTER TABLE images CHANGE COLUMN metadata metadata VARCHAR(400) NULL DEFAULT NULL AFTER description;"
    echo "      Deny back null to column 'vim_interface_id' in 'instance_interfaces'"
    sql "ALTER TABLE instance_interfaces CHANGE COLUMN vim_interface_id vim_interface_id VARCHAR(36) NOT NULL COMMENT 'vim identity for that interface' AFTER interface_id; "
    echo "       Delete column config to table 'datacenters'"
    sql "ALTER TABLE datacenters DROP COLUMN config;"
    echo "       Delete column datacenter_id to table 'vim_tenants'"
    sql "ALTER TABLE vim_tenants DROP COLUMN datacenter_id, DROP FOREIGN KEY FK_vim_tenants_datacenters;"
    sql "ALTER TABLE vim_tenants CHANGE COLUMN vim_tenant_name name VARCHAR(36) NULL DEFAULT NULL COMMENT '' AFTER uuid"
    sql "ALTER TABLE vim_tenants ALTER name DROP DEFAULT;"
    sql "ALTER TABLE vim_tenants CHANGE COLUMN name name VARCHAR(36) NOT NULL AFTER uuid" || ! echo "Warning changing column name at vim_tenants!"
    sql "ALTER TABLE vim_tenants ADD UNIQUE INDEX name (name);" || ! echo "Warning add unique index name at vim_tenants!"
    sql "ALTER TABLE vim_tenants ALTER vim_tenant_id DROP DEFAULT;"
    sql "ALTER TABLE vim_tenants CHANGE COLUMN vim_tenant_id vim_tenant_id VARCHAR(36) NOT NULL COMMENT 'Tenant ID in the VIM DB' AFTER name;" ||
        ! echo "Warning changing column vim_tenant_id at vim_tenants!"
    sql "ALTER TABLE vim_tenants ADD UNIQUE INDEX vim_tenant_id (vim_tenant_id);" ||
        ! echo "Warning add unique index vim_tenant_id at vim_tenants!"
    sql "DELETE FROM schema_version WHERE version_int='3';"
}

function upgrade_to_4(){
    # echo "    upgrade database from version 0.3 to version 0.4"
    echo "      Enlarge graph field at tables 'sce_vnfs', 'sce_nets'"
    for table in sce_vnfs sce_nets
    do
        sql "ALTER TABLE $table CHANGE COLUMN graph graph VARCHAR(2000) NULL DEFAULT NULL AFTER modified_at;"
    done
    sql "ALTER TABLE datacenters CHANGE COLUMN type type VARCHAR(36) NOT NULL DEFAULT 'openvim' AFTER description;"
    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) VALUES (4, '0.4', '0.3.5', 'enlarge graph field at sce_vnfs/nets', '2015-10-20');"
}

function downgrade_from_4(){
    # echo "    downgrade database from version 0.4 to version 0.3"
    echo "      Shorten back graph field at tables 'sce_vnfs', 'sce_nets'"
    for table in sce_vnfs sce_nets
    do
        sql "ALTER TABLE $table CHANGE COLUMN graph graph VARCHAR(2000) NULL DEFAULT NULL AFTER modified_at;"
    done
    sql "ALTER TABLE datacenters CHANGE COLUMN type type ENUM('openvim','openstack') NOT NULL DEFAULT 'openvim' AFTER description;"
    sql "DELETE FROM schema_version WHERE version_int='4';"
}

function upgrade_to_5(){
    # echo "    upgrade database from version 0.4 to version 0.5"
    echo "      Add 'mac' field for bridge interfaces in table 'interfaces'"
    sql "ALTER TABLE interfaces ADD COLUMN mac CHAR(18) NULL DEFAULT NULL AFTER model;"
    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) VALUES (5, '0.5', '0.4.1', 'Add mac address for bridge interfaces', '2015-12-14');"
}
function downgrade_from_5(){
    # echo "    downgrade database from version 0.5 to version 0.4"
    echo "      Remove 'mac' field for bridge interfaces in table 'interfaces'"
    sql "ALTER TABLE interfaces DROP COLUMN mac;"
    sql "DELETE FROM schema_version WHERE version_int='5';"
}

function upgrade_to_6(){
    # echo "    upgrade database from version 0.5 to version 0.6"
    echo "      Add 'descriptor' field text to 'vnfd', 'scenarios'"
    sql "ALTER TABLE vnfs ADD COLUMN descriptor TEXT NULL DEFAULT NULL COMMENT 'Original text descriptor used for create the VNF' AFTER class;"
    sql "ALTER TABLE scenarios ADD COLUMN descriptor TEXT NULL DEFAULT NULL COMMENT 'Original text descriptor used for create the scenario' AFTER modified_at;"
    echo "      Add 'last_error', 'vim_info' to 'instance_vms', 'instance_nets'"
    sql "ALTER TABLE instance_vms  ADD COLUMN error_msg VARCHAR(1024) NULL DEFAULT NULL AFTER status;"
    sql "ALTER TABLE instance_vms  ADD COLUMN vim_info TEXT NULL DEFAULT NULL AFTER error_msg;"
    sql "ALTER TABLE instance_vms  CHANGE COLUMN status status ENUM('ACTIVE','INACTIVE','BUILD','ERROR','VIM_ERROR','PAUSED','SUSPENDED','DELETED') NOT NULL DEFAULT 'BUILD' AFTER vim_vm_id;"
    sql "ALTER TABLE instance_nets ADD COLUMN error_msg VARCHAR(1024) NULL DEFAULT NULL AFTER status;"
    sql "ALTER TABLE instance_nets ADD COLUMN vim_info TEXT NULL DEFAULT NULL AFTER error_msg;"
    sql "ALTER TABLE instance_nets CHANGE COLUMN status status ENUM('ACTIVE','DOWN','BUILD','ERROR','VIM_ERROR','INACTIVE','DELETED') NOT NULL DEFAULT 'BUILD' AFTER instance_scenario_id;"
    echo "      Add 'mac_address', 'ip_address', 'vim_info' to 'instance_interfaces'"
    sql "ALTER TABLE instance_interfaces ADD COLUMN mac_address VARCHAR(32) NULL DEFAULT NULL AFTER vim_interface_id, ADD COLUMN ip_address VARCHAR(64) NULL DEFAULT NULL AFTER mac_address, ADD COLUMN vim_info TEXT NULL DEFAULT NULL AFTER ip_address;"
    echo "      Add 'sce_vnf_id','datacenter_id','vim_tenant_id' field to 'instance_vnfs'"
    sql "ALTER TABLE instance_vnfs ADD COLUMN sce_vnf_id VARCHAR(36) NULL DEFAULT NULL AFTER vnf_id, ADD CONSTRAINT FK_instance_vnfs_sce_vnfs FOREIGN KEY (sce_vnf_id) REFERENCES sce_vnfs (uuid) ON UPDATE CASCADE ON DELETE SET NULL;"
    sql "ALTER TABLE instance_vnfs ADD COLUMN vim_tenant_id VARCHAR(36) NULL DEFAULT NULL AFTER sce_vnf_id, ADD CONSTRAINT FK_instance_vnfs_vim_tenants FOREIGN KEY (vim_tenant_id) REFERENCES vim_tenants (uuid) ON UPDATE RESTRICT ON DELETE RESTRICT;"
    sql "ALTER TABLE instance_vnfs ADD COLUMN datacenter_id VARCHAR(36) NULL DEFAULT NULL AFTER vim_tenant_id, ADD CONSTRAINT FK_instance_vnfs_datacenters FOREIGN KEY (datacenter_id) REFERENCES datacenters (uuid) ON UPDATE RESTRICT ON DELETE RESTRICT;"
    echo "      Add 'sce_net_id','net_id','datacenter_id','vim_tenant_id' field to 'instance_nets'"
    sql "ALTER TABLE instance_nets ADD COLUMN sce_net_id VARCHAR(36) NULL DEFAULT NULL AFTER instance_scenario_id, ADD CONSTRAINT FK_instance_nets_sce_nets FOREIGN KEY (sce_net_id) REFERENCES sce_nets (uuid) ON UPDATE CASCADE ON DELETE SET NULL;"
    sql "ALTER TABLE instance_nets ADD COLUMN net_id VARCHAR(36) NULL DEFAULT NULL AFTER sce_net_id, ADD CONSTRAINT FK_instance_nets_nets FOREIGN KEY (net_id) REFERENCES nets (uuid) ON UPDATE CASCADE ON DELETE SET NULL;"
    sql "ALTER TABLE instance_nets ADD COLUMN vim_tenant_id VARCHAR(36) NULL DEFAULT NULL AFTER net_id, ADD CONSTRAINT FK_instance_nets_vim_tenants FOREIGN KEY (vim_tenant_id) REFERENCES vim_tenants (uuid) ON UPDATE RESTRICT ON DELETE RESTRICT;"
    sql "ALTER TABLE instance_nets ADD COLUMN datacenter_id VARCHAR(36) NULL DEFAULT NULL AFTER vim_tenant_id, ADD CONSTRAINT FK_instance_nets_datacenters FOREIGN KEY (datacenter_id) REFERENCES datacenters (uuid) ON UPDATE RESTRICT ON DELETE RESTRICT;"
    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) VALUES (6, '0.6', '0.4.2', 'Adding VIM status info', '2015-12-22');"
}
function downgrade_from_6(){
    # echo "    downgrade database from version 0.6 to version 0.5"
    echo "      Remove 'descriptor' field from 'vnfd', 'scenarios' tables"
    sql "ALTER TABLE vnfs      DROP COLUMN descriptor;"
    sql "ALTER TABLE scenarios DROP COLUMN descriptor;"
    echo "      Remove 'last_error', 'vim_info' from 'instance_vms', 'instance_nets'"
    sql "ALTER TABLE instance_vms  DROP COLUMN error_msg, DROP COLUMN vim_info;"
    sql "ALTER TABLE instance_vms  CHANGE COLUMN status status ENUM('ACTIVE','PAUSED','INACTIVE','CREATING','ERROR','DELETING') NOT NULL DEFAULT 'CREATING' AFTER vim_vm_id;"
    sql "ALTER TABLE instance_nets DROP COLUMN error_msg, DROP COLUMN vim_info;"
    sql "ALTER TABLE instance_nets CHANGE COLUMN status status ENUM('ACTIVE','DOWN','BUILD','ERROR') NOT NULL DEFAULT 'BUILD' AFTER instance_scenario_id;"
    echo "      Remove 'mac_address', 'ip_address', 'vim_info' from 'instance_interfaces'"
    sql "ALTER TABLE instance_interfaces DROP COLUMN mac_address, DROP COLUMN ip_address, DROP COLUMN vim_info;"
    echo "      Remove 'sce_vnf_id','datacenter_id','vim_tenant_id' field from 'instance_vnfs'"
    sql "ALTER TABLE instance_vnfs DROP COLUMN sce_vnf_id, DROP FOREIGN KEY FK_instance_vnfs_sce_vnfs;"
    sql "ALTER TABLE instance_vnfs DROP COLUMN vim_tenant_id, DROP FOREIGN KEY FK_instance_vnfs_vim_tenants;"
    sql "ALTER TABLE instance_vnfs DROP COLUMN datacenter_id, DROP FOREIGN KEY FK_instance_vnfs_datacenters;"
    echo "      Remove 'sce_net_id','net_id','datacenter_id','vim_tenant_id' field from 'instance_nets'"
    sql "ALTER TABLE instance_nets DROP COLUMN sce_net_id, DROP FOREIGN KEY FK_instance_nets_sce_nets;"
    sql "ALTER TABLE instance_nets DROP COLUMN net_id, DROP FOREIGN KEY FK_instance_nets_nets;"
    sql "ALTER TABLE instance_nets DROP COLUMN vim_tenant_id, DROP FOREIGN KEY FK_instance_nets_vim_tenants;"
    sql "ALTER TABLE instance_nets DROP COLUMN datacenter_id, DROP FOREIGN KEY FK_instance_nets_datacenters;"
    sql "DELETE FROM schema_version WHERE version_int='6';"
}

function upgrade_to_7(){
    # echo "    upgrade database from version 0.6 to version 0.7"
    echo "      Change created_at, modified_at from timestamp to unix float at all database"
    for table in datacenters datacenter_nets instance_nets instance_scenarios instance_vms instance_vnfs interfaces nets nfvo_tenants scenarios sce_interfaces sce_nets sce_vnfs tenants_datacenters vim_tenants vms vnfs uuids
    do
         echo -en "        $table               \r"
         sql "ALTER TABLE $table ADD COLUMN created_at_ DOUBLE NOT NULL after created_at;"
         echo "UPDATE $table SET created_at_=unix_timestamp(created_at);"
         sql "ALTER TABLE $table DROP COLUMN created_at, CHANGE COLUMN created_at_ created_at DOUBLE NOT NULL;"
         [[ $table == uuids ]] || sql "ALTER TABLE $table CHANGE COLUMN modified_at modified_at DOUBLE NULL DEFAULT NULL;"
    done
    
    echo "      Add 'descriptor' field text to 'vnfd', 'scenarios'"
    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) VALUES (7, '0.7', '0.4.3', 'Changing created_at time at database', '2016-01-25');"
}
function downgrade_from_7(){
    # echo "    downgrade database from version 0.7 to version 0.6"
    echo "      Change back created_at, modified_at from unix float to timestamp at all database"
    for table in datacenters datacenter_nets instance_nets instance_scenarios instance_vms instance_vnfs interfaces nets nfvo_tenants scenarios sce_interfaces sce_nets sce_vnfs tenants_datacenters vim_tenants vms vnfs uuids
    do
         echo -en "        $table               \r"
         sql "ALTER TABLE $table ADD COLUMN created_at_ TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP after created_at;"
         echo "UPDATE $table SET created_at_=from_unixtime(created_at);"
         sql "ALTER TABLE $table DROP COLUMN created_at, CHANGE COLUMN created_at_ created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;"
         [[ $table == uuids ]] || sql "ALTER TABLE $table CHANGE COLUMN modified_at modified_at TIMESTAMP NULL DEFAULT NULL;"
    done
    echo "      Remove 'descriptor' field from 'vnfd', 'scenarios' tables"
    sql "DELETE FROM schema_version WHERE version_int='7';"
}

function upgrade_to_8(){
    # echo "    upgrade database from version 0.7 to version 0.8"
    echo "      Change enalarge name, description to 255 at all database"
    for table in datacenters datacenter_nets flavors images instance_scenarios nets nfvo_tenants scenarios sce_nets sce_vnfs vms vnfs
    do
         echo -en "        $table               \r"
         sql "ALTER TABLE $table CHANGE COLUMN name name VARCHAR(255) NOT NULL;"
         sql "ALTER TABLE $table CHANGE COLUMN description description VARCHAR(255) NULL DEFAULT NULL;"
    done
    echo -en "        interfaces           \r"
    sql "ALTER TABLE interfaces CHANGE COLUMN internal_name internal_name VARCHAR(255) NOT NULL, CHANGE COLUMN external_name external_name VARCHAR(255) NULL DEFAULT NULL;"
    sql "ALTER TABLE vim_tenants CHANGE COLUMN vim_tenant_name vim_tenant_name VARCHAR(64) NULL DEFAULT NULL;"
    echo -en "        vim_tenants          \r"
    sql "ALTER TABLE vim_tenants CHANGE COLUMN user user VARCHAR(64) NULL DEFAULT NULL, CHANGE COLUMN passwd passwd VARCHAR(64) NULL DEFAULT NULL;"
    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) VALUES (8, '0.8', '0.4.32', 'Enlarging name at database', '2016-02-01');"
}
function downgrade_from_8(){
    # echo "    downgrade database from version 0.8 to version 0.7"
    echo "      Change back name,description to shorter length at all database"
    for table in datacenters datacenter_nets flavors images instance_scenarios nets nfvo_tenants scenarios sce_nets sce_vnfs vms vnfs
    do
         name_length=50
         [[ $table == flavors ]] || [[ $table == images ]] || name_length=36 
         echo -en "        $table               \r"
         sql "ALTER TABLE $table CHANGE COLUMN name name VARCHAR($name_length) NOT NULL;"
         sql "ALTER TABLE $table CHANGE COLUMN description description VARCHAR(100) NULL DEFAULT NULL;"
    done
    echo -en "        interfaces           \r"
    sql "ALTER TABLE interfaces CHANGE COLUMN internal_name internal_name VARCHAR(25) NOT NULL, CHANGE COLUMN external_name external_name VARCHAR(25) NULL DEFAULT NULL;"
    echo -en "        vim_tenants          \r"
    sql "ALTER TABLE vim_tenants CHANGE COLUMN vim_tenant_name vim_tenant_name VARCHAR(36) NULL DEFAULT NULL;"
    sql "ALTER TABLE vim_tenants CHANGE COLUMN user user VARCHAR(36) NULL DEFAULT NULL, CHANGE COLUMN passwd passwd VARCHAR(50) NULL DEFAULT NULL;"
    sql "DELETE FROM schema_version WHERE version_int='8';"
}
function upgrade_to_9(){
    # echo "    upgrade database from version 0.8 to version 0.9"
    echo "      Add more status to 'instance_vms'"
    sql "ALTER TABLE instance_vms CHANGE COLUMN status status ENUM('ACTIVE:NoMgmtIP','ACTIVE','INACTIVE','BUILD','ERROR','VIM_ERROR','PAUSED','SUSPENDED','DELETED') NOT NULL DEFAULT 'BUILD';"
    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) VALUES (9, '0.9', '0.4.33', 'Add ACTIVE:NoMgmtIP to instance_vms table', '2016-02-05');"
}
function downgrade_from_9(){
    # echo "    downgrade database from version 0.9 to version 0.8"
    echo "      Add more status to 'instance_vms'"
    sql "ALTER TABLE instance_vms CHANGE COLUMN status status ENUM('ACTIVE','INACTIVE','BUILD','ERROR','VIM_ERROR','PAUSED','SUSPENDED','DELETED') NOT NULL DEFAULT 'BUILD';"
    sql "DELETE FROM schema_version WHERE version_int='9';"
}
function upgrade_to_10(){
    # echo "    upgrade database from version 0.9 to version 0.10"
    echo "      add tenant to 'vnfs'"
    sql "ALTER TABLE vnfs ADD COLUMN tenant_id VARCHAR(36) NULL DEFAULT NULL AFTER name, ADD CONSTRAINT FK_vnfs_nfvo_tenants FOREIGN KEY (tenant_id) REFERENCES nfvo_tenants (uuid) ON UPDATE CASCADE ON DELETE SET NULL, CHANGE COLUMN public public ENUM('true','false') NOT NULL DEFAULT 'false' AFTER physical, DROP INDEX name, DROP INDEX path, DROP COLUMN path;"
    sql "ALTER TABLE scenarios DROP FOREIGN KEY FK_scenarios_nfvo_tenants;"
    sql "ALTER TABLE scenarios CHANGE COLUMN nfvo_tenant_id tenant_id VARCHAR(36) NULL DEFAULT NULL after name, ADD CONSTRAINT FK_scenarios_nfvo_tenants FOREIGN KEY (tenant_id) REFERENCES nfvo_tenants (uuid);"
    sql "ALTER TABLE instance_scenarios DROP FOREIGN KEY FK_instance_scenarios_nfvo_tenants;"
    sql "ALTER TABLE instance_scenarios CHANGE COLUMN nfvo_tenant_id tenant_id VARCHAR(36) NULL DEFAULT NULL after name, ADD CONSTRAINT FK_instance_scenarios_nfvo_tenants FOREIGN KEY (tenant_id) REFERENCES nfvo_tenants (uuid);"
    echo "      rename 'vim_tenants' table to 'datacenter_tenants'"
    echo "RENAME TABLE vim_tenants TO datacenter_tenants;"
    for table in tenants_datacenters instance_scenarios instance_vnfs instance_nets
    do
        NULL="NOT NULL"
        [[ $table == instance_vnfs ]] && NULL="NULL DEFAULT NULL"
        sql "ALTER TABLE ${table} DROP FOREIGN KEY FK_${table}_vim_tenants;"
        sql "ALTER TABLE ${table} ALTER vim_tenant_id DROP DEFAULT;"
        sql "ALTER TABLE ${table} CHANGE COLUMN vim_tenant_id datacenter_tenant_id VARCHAR(36)  ${NULL} AFTER datacenter_id, ADD CONSTRAINT FK_${table}_datacenter_tenants FOREIGN KEY (datacenter_tenant_id) REFERENCES datacenter_tenants (uuid); "
    done    
    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) VALUES (10, '0.10', '0.4.36', 'tenant management of vnfs,scenarios', '2016-03-08');"
}

function downgrade_from_10(){
    # echo "    downgrade database from version 0.10 to version 0.9"
    echo "      remove tenant from 'vnfs'"
    sql "ALTER TABLE vnfs DROP COLUMN tenant_id, DROP FOREIGN KEY FK_vnfs_nfvo_tenants, ADD UNIQUE INDEX name (name), ADD COLUMN path VARCHAR(100) NULL DEFAULT NULL COMMENT 'Path where the YAML descriptor of the VNF can be found. NULL if it is a physical network function.' AFTER name, ADD UNIQUE INDEX path (path), CHANGE COLUMN public public ENUM('true','false') NOT NULL DEFAULT 'true' AFTER physical;"
    sql "ALTER TABLE scenarios DROP FOREIGN KEY FK_scenarios_nfvo_tenants;"
    sql "ALTER TABLE scenarios CHANGE COLUMN tenant_id nfvo_tenant_id VARCHAR(36) NULL DEFAULT NULL after name, ADD CONSTRAINT FK_scenarios_nfvo_tenants FOREIGN KEY (nfvo_tenant_id) REFERENCES nfvo_tenants (uuid);"
    sql "ALTER TABLE instance_scenarios DROP FOREIGN KEY FK_instance_scenarios_nfvo_tenants;"
    sql "ALTER TABLE instance_scenarios CHANGE COLUMN tenant_id nfvo_tenant_id VARCHAR(36) NULL DEFAULT NULL after name, ADD CONSTRAINT FK_instance_scenarios_nfvo_tenants FOREIGN KEY (nfvo_tenant_id) REFERENCES nfvo_tenants (uuid);"
    echo "      rename back 'datacenter_tenants' table to 'vim_tenants'"
    echo "RENAME TABLE datacenter_tenants TO vim_tenants;"
    for table in tenants_datacenters instance_scenarios instance_vnfs instance_nets
    do
        sql "ALTER TABLE ${table} DROP FOREIGN KEY FK_${table}_datacenter_tenants;"
        NULL="NOT NULL"
        [[ $table == instance_vnfs ]] && NULL="NULL DEFAULT NULL"
        sql "ALTER TABLE ${table} ALTER datacenter_tenant_id DROP DEFAULT;"
        sql "ALTER TABLE ${table} CHANGE COLUMN datacenter_tenant_id vim_tenant_id VARCHAR(36) $NULL AFTER datacenter_id, ADD CONSTRAINT FK_${table}_vim_tenants FOREIGN KEY (vim_tenant_id) REFERENCES vim_tenants (uuid); "
    done    
    sql "DELETE FROM schema_version WHERE version_int='10';"
}

function upgrade_to_11(){
    # echo "    upgrade database from version 0.10 to version 0.11"
    echo "      remove unique name at 'scenarios', 'instance_scenarios'"
    sql "ALTER TABLE scenarios DROP INDEX name;"
    sql "ALTER TABLE instance_scenarios DROP INDEX name;"
    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) VALUES (11, '0.11', '0.4.43', 'remove unique name at scenarios,instance_scenarios', '2016-07-18');"
}
function downgrade_from_11(){
    # echo "    downgrade database from version 0.11 to version 0.10"
    echo "      add unique name at 'scenarios', 'instance_scenarios'"
    sql "ALTER TABLE scenarios ADD UNIQUE INDEX name (name);"
    sql "ALTER TABLE instance_scenarios ADD UNIQUE INDEX name (name);"
    sql "DELETE FROM schema_version WHERE version_int='11';"
}

function upgrade_to_12(){
    # echo "    upgrade database from version 0.11 to version 0.12"
    echo "      create ip_profiles table, with foreign keys to all nets tables, and add ip_address column to 'interfaces' and 'sce_interfaces'"
    sql "CREATE TABLE IF NOT EXISTS ip_profiles (
	id INT(11) NOT NULL AUTO_INCREMENT,
	net_id VARCHAR(36) NULL DEFAULT NULL,
	sce_net_id VARCHAR(36) NULL DEFAULT NULL,
	instance_net_id VARCHAR(36) NULL DEFAULT NULL,
	ip_version ENUM('IPv4','IPv6') NOT NULL DEFAULT 'IPv4',
	subnet_address VARCHAR(64) NULL DEFAULT NULL,
	gateway_address VARCHAR(64) NULL DEFAULT NULL,
	dns_address VARCHAR(64) NULL DEFAULT NULL,
	dhcp_enabled ENUM('true','false') NOT NULL DEFAULT 'true',
	dhcp_start_address VARCHAR(64) NULL DEFAULT NULL,
	dhcp_count INT(11) NULL DEFAULT NULL,
	PRIMARY KEY (id),
	CONSTRAINT FK_ipprofiles_nets FOREIGN KEY (net_id) REFERENCES nets (uuid) ON DELETE CASCADE,
	CONSTRAINT FK_ipprofiles_scenets FOREIGN KEY (sce_net_id) REFERENCES sce_nets (uuid) ON DELETE CASCADE,
	CONSTRAINT FK_ipprofiles_instancenets FOREIGN KEY (instance_net_id) REFERENCES instance_nets (uuid) ON DELETE CASCADE  )
        COMMENT='Table containing the IP parameters of a network, either a net, a sce_net or and instance_net.'
        COLLATE='utf8_general_ci'
        ENGINE=InnoDB;"
    sql "ALTER TABLE interfaces ADD COLUMN ip_address VARCHAR(64) NULL DEFAULT NULL AFTER mac;"
    sql "ALTER TABLE sce_interfaces ADD COLUMN ip_address VARCHAR(64) NULL DEFAULT NULL AFTER interface_id;"
    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) VALUES (12, '0.12', '0.4.46', 'create ip_profiles table, with foreign keys to all nets tables, and add ip_address column to interfaces and sce_interfaces', '2016-08-29');"
}
function downgrade_from_12(){
    # echo "    downgrade database from version 0.12 to version 0.11"
    echo "      delete ip_profiles table, and remove ip_address column in 'interfaces' and 'sce_interfaces'"
    sql "DROP TABLE ip_profiles;"
    sql "ALTER TABLE interfaces DROP COLUMN ip_address;"
    sql "ALTER TABLE sce_interfaces DROP COLUMN ip_address;"
    sql "DELETE FROM schema_version WHERE version_int='12';"
}

function upgrade_to_13(){
    # echo "    upgrade database from version 0.12 to version 0.13"
    echo "      add cloud_config at 'scenarios', 'instance_scenarios'"
    sql "ALTER TABLE scenarios ADD COLUMN cloud_config MEDIUMTEXT NULL DEFAULT NULL AFTER descriptor;"
    sql "ALTER TABLE instance_scenarios ADD COLUMN cloud_config MEDIUMTEXT NULL DEFAULT NULL AFTER modified_at;"
    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) VALUES (13, '0.13', '0.4.47', 'insert cloud-config at scenarios,instance_scenarios', '2016-08-30');"
}
function downgrade_from_13(){
    # echo "    downgrade database from version 0.13 to version 0.12"
    echo "      remove cloud_config at 'scenarios', 'instance_scenarios'"
    sql "ALTER TABLE scenarios DROP COLUMN cloud_config;"
    sql "ALTER TABLE instance_scenarios DROP COLUMN cloud_config;"
    sql "DELETE FROM schema_version WHERE version_int='13';"
}

function upgrade_to_14(){
    # echo "    upgrade database from version 0.13 to version 0.14"
    echo "      remove unique index vim_net_id, instance_scenario_id at table 'instance_nets'"
    sql "ALTER TABLE instance_nets DROP INDEX vim_net_id_instance_scenario_id;"
    sql "ALTER TABLE instance_nets CHANGE COLUMN external created ENUM('true','false') NOT NULL DEFAULT 'false' COMMENT 'Created or already exists at VIM' AFTER multipoint;"
    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) VALUES (14, '0.14', '0.4.57', 'remove unique index vim_net_id, instance_scenario_id', '2016-09-26');"
}
function downgrade_from_14(){
    # echo "    downgrade database from version 0.14 to version 0.13"
    echo "      remove cloud_config at 'scenarios', 'instance_scenarios'"
    sql "ALTER TABLE instance_nets ADD UNIQUE INDEX vim_net_id_instance_scenario_id (vim_net_id, instance_scenario_id);"
    sql "ALTER TABLE instance_nets CHANGE COLUMN created external ENUM('true','false') NOT NULL DEFAULT 'false' COMMENT 'If external, means that it already exists at VIM' AFTER multipoint;"
    sql "DELETE FROM schema_version WHERE version_int='14';"
}

function upgrade_to_15(){
    # echo "    upgrade database from version 0.14 to version 0.15"
    echo "      add columns 'universal_name' and 'checksum' at table 'images', add unique index universal_name_checksum, and change location to allow NULL; change column 'image_path' in table 'vms' to allow NULL"
    sql "ALTER TABLE images ADD COLUMN checksum VARCHAR(32) NULL DEFAULT NULL AFTER name;"
    sql "ALTER TABLE images ALTER location DROP DEFAULT;"
    sql "ALTER TABLE images ADD COLUMN universal_name VARCHAR(255) NULL AFTER name, CHANGE COLUMN location location VARCHAR(200) NULL AFTER checksum, ADD UNIQUE INDEX universal_name_checksum (universal_name, checksum);"
    sql "ALTER TABLE vms ALTER image_path DROP DEFAULT;"
    sql "ALTER TABLE vms CHANGE COLUMN image_path image_path VARCHAR(100) NULL COMMENT 'Path where the image of the VM is located' AFTER image_id;"
    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) VALUES (15, '0.15', '0.4.59', 'add columns universal_name and checksum at table images, add unique index universal_name_checksum, and change location to allow NULL; change column image_path in table vms to allow NULL', '2016-09-27');"
}
function downgrade_from_15(){
    # echo "    downgrade database from version 0.15 to version 0.14"
    echo "      remove columns 'universal_name' and 'checksum' from table 'images', remove index universal_name_checksum, change location NOT NULL; change column 'image_path' in table 'vms' to NOT NULL"
    sql "ALTER TABLE images DROP INDEX universal_name_checksum;"
    sql "ALTER TABLE images ALTER location DROP DEFAULT;"
    sql "ALTER TABLE images CHANGE COLUMN location location VARCHAR(200) NOT NULL AFTER checksum;"
    sql "ALTER TABLE images DROP COLUMN universal_name;"
    sql "ALTER TABLE images DROP COLUMN checksum;"
    sql "ALTER TABLE vms ALTER image_path DROP DEFAULT;"
    sql "ALTER TABLE vms CHANGE COLUMN image_path image_path VARCHAR(100) NOT NULL COMMENT 'Path where the image of the VM is located' AFTER image_id;"
    sql "DELETE FROM schema_version WHERE version_int='15';"
}

function upgrade_to_16(){
    # echo "    upgrade database from version 0.15 to version 0.16"
    echo "      add column 'config' at table 'datacenter_tenants', enlarge 'vim_tenant_name/id'"
    sql "ALTER TABLE datacenter_tenants ADD COLUMN config VARCHAR(4000) NULL DEFAULT NULL AFTER passwd;"
    sql "ALTER TABLE datacenter_tenants CHANGE COLUMN vim_tenant_name vim_tenant_name VARCHAR(256) NULL DEFAULT NULL AFTER datacenter_id;"
    sql "ALTER TABLE datacenter_tenants CHANGE COLUMN vim_tenant_id vim_tenant_id VARCHAR(256) NULL DEFAULT NULL COMMENT 'Tenant ID at VIM' AFTER vim_tenant_name;"
    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) VALUES (16, '0.16', '0.5.2', 'enlarge vim_tenant_name and id. New config at datacenter_tenants', '2016-10-11');"
}
function downgrade_from_16(){
    # echo "    downgrade database from version 0.16 to version 0.15"
    echo "      remove column 'config' at table 'datacenter_tenants', restoring lenght 'vim_tenant_name/id'"
    sql "ALTER TABLE datacenter_tenants DROP COLUMN config;"
    sql "ALTER TABLE datacenter_tenants CHANGE COLUMN vim_tenant_name vim_tenant_name VARCHAR(64) NULL DEFAULT NULL AFTER datacenter_id;"
    sql "ALTER TABLE datacenter_tenants CHANGE COLUMN vim_tenant_id vim_tenant_id VARCHAR(36) NULL DEFAULT NULL COMMENT 'Tenant ID at VIM' AFTER vim_tenant_name;"
    sql "DELETE FROM schema_version WHERE version_int='16';"
}

function upgrade_to_17(){
    # echo "    upgrade database from version 0.16 to version 0.17"
    echo "      add column 'extended' at table 'datacenter_flavors'"
    sql "ALTER TABLE datacenters_flavors ADD extended varchar(2000) NULL COMMENT 'Extra description json format of additional devices';"
    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) VALUES (17, '0.17', '0.5.3', 'Extra description json format of additional devices in datacenter_flavors', '2016-12-20');"
}
function downgrade_from_17(){
    # echo "    downgrade database from version 0.17 to version 0.16"
    echo "      remove column 'extended' from table 'datacenter_flavors'"
    sql "ALTER TABLE datacenters_flavors DROP COLUMN extended;"
    sql "DELETE FROM schema_version WHERE version_int='17';"
}

function upgrade_to_18(){
    # echo "    upgrade database from version 0.17 to version 0.18"
    echo "      add columns 'floating_ip' and 'port_security' at tables 'interfaces' and 'instance_interfaces'"
    sql "ALTER TABLE interfaces ADD floating_ip BOOL DEFAULT 0 NOT NULL COMMENT 'Indicates if a floating_ip must be associated to this interface';"
    sql "ALTER TABLE interfaces ADD port_security BOOL DEFAULT 1 NOT NULL COMMENT 'Indicates if port security must be enabled or disabled. By default it is enabled';"
    sql "ALTER TABLE instance_interfaces ADD floating_ip BOOL DEFAULT 0 NOT NULL COMMENT 'Indicates if a floating_ip must be associated to this interface';"
    sql "ALTER TABLE instance_interfaces ADD port_security BOOL DEFAULT 1 NOT NULL COMMENT 'Indicates if port security must be enabled or disabled. By default it is enabled';"
    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) VALUES (18, '0.18', '0.5.4', 'Add columns \'floating_ip\' and \'port_security\' at tables \'interfaces\' and \'instance_interfaces\'', '2017-01-09');"
}
function downgrade_from_18(){
    # echo "    downgrade database from version 0.18 to version 0.17"
    echo "      remove columns 'floating_ip' and 'port_security' from tables 'interfaces' and 'instance_interfaces'"
    sql "ALTER TABLE interfaces DROP COLUMN floating_ip;"
    sql "ALTER TABLE interfaces DROP COLUMN port_security;"
    sql "ALTER TABLE instance_interfaces DROP COLUMN floating_ip;"
    sql "ALTER TABLE instance_interfaces DROP COLUMN port_security;"
    sql "DELETE FROM schema_version WHERE version_int='18';"
}

function upgrade_to_19(){
    # echo "    upgrade database from version 0.18 to version 0.19"
    echo "      add column 'boot_data' at table 'vms'"
    sql "ALTER TABLE vms ADD COLUMN boot_data TEXT NULL DEFAULT NULL AFTER image_path;"
    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) VALUES (19, '0.19', '0.5.5', 'Extra Boot-data content at VNFC (vms)', '2017-01-11');"
}
function downgrade_from_19(){
    # echo "    downgrade database from version 0.19 to version 0.18"
    echo "      remove column 'boot_data' from table 'vms'"
    sql "ALTER TABLE vms DROP COLUMN boot_data;"
    sql "DELETE FROM schema_version WHERE version_int='19';"
}

function upgrade_to_20(){
    # echo "    upgrade database from version 0.19 to version 0.20"
    echo "      add column 'sdn_net_id' at table 'instance_nets' and columns 'sdn_port_id', 'compute_node', 'pci' and 'vlan' to table 'instance_interfaces'"
    sql "ALTER TABLE instance_nets ADD sdn_net_id varchar(36) DEFAULT NULL NULL COMMENT 'Network id in ovim';"
    sql "ALTER TABLE instance_interfaces ADD sdn_port_id varchar(36) DEFAULT NULL NULL COMMENT 'Port id in ovim';"
    sql "ALTER TABLE instance_interfaces ADD compute_node varchar(100) DEFAULT NULL NULL COMMENT 'Compute node id used to specify the SDN port mapping';"
    sql "ALTER TABLE instance_interfaces ADD pci varchar(12) DEFAULT NULL NULL COMMENT 'PCI of the physical port in the host';"
    sql "ALTER TABLE instance_interfaces ADD vlan SMALLINT UNSIGNED DEFAULT NULL NULL COMMENT 'VLAN tag used by the port';"
    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) VALUES (20, '0.20', '0.5.9', 'Added columns to store dataplane connectivity info', '2017-03-13');"
}
function downgrade_from_20(){
    # echo "    downgrade database from version 0.20 to version 0.19"
    echo "      remove column 'sdn_net_id' at table 'instance_nets' and columns 'sdn_port_id', 'compute_node', 'pci' and 'vlan' to table 'instance_interfaces'"
    sql "ALTER TABLE instance_nets DROP COLUMN sdn_net_id;"
    sql "ALTER TABLE instance_interfaces DROP COLUMN vlan;"
    sql "ALTER TABLE instance_interfaces DROP COLUMN pci;"
    sql "ALTER TABLE instance_interfaces DROP COLUMN compute_node;"
    sql "ALTER TABLE instance_interfaces DROP COLUMN sdn_port_id;"
    sql "DELETE FROM schema_version WHERE version_int='20';"
}

function upgrade_to_21(){
    # echo "    upgrade database from version 0.20 to version 0.21"
    echo "      edit 'instance_nets' to allow instance_scenario_id=None"
    sql "ALTER TABLE instance_nets MODIFY COLUMN instance_scenario_id varchar(36) NULL;"
    echo "      enlarge column 'dns_address' at table 'ip_profiles'"
    sql "ALTER TABLE ip_profiles MODIFY dns_address varchar(255) DEFAULT NULL NULL "\
         "comment 'dns ip list separated by semicolon';"
    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) VALUES (21, '0.21', '0.5.15', 'Edit instance_nets to allow instance_scenario_id=None and enlarge column dns_address at table ip_profiles', '2017-06-02');"
}
function downgrade_from_21(){
    # echo "    downgrade database from version 0.21 to version 0.20"
    echo "      edit 'instance_nets' to disallow instance_scenario_id=None"
    #Delete all lines with a instance_scenario_id=NULL in order to disable this option
    sql "DELETE FROM instance_nets WHERE instance_scenario_id IS NULL;"
    sql "ALTER TABLE instance_nets MODIFY COLUMN instance_scenario_id varchar(36) NOT NULL;"
    echo "      shorten column 'dns_address' at table 'ip_profiles'"
    sql "ALTER TABLE ip_profiles MODIFY dns_address varchar(64) DEFAULT NULL NULL;"
    sql "DELETE FROM schema_version WHERE version_int='21';"
}

function upgrade_to_22(){
    # echo "    upgrade database from version 0.21 to version 0.22"
    echo "      Changed type of ram in 'flavors' from SMALLINT to MEDIUMINT"
    sql "ALTER TABLE flavors CHANGE COLUMN ram ram MEDIUMINT(7) UNSIGNED NULL DEFAULT NULL AFTER disk;"
    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) VALUES (22, '0.22', '0.5.16', 'Changed type of ram in flavors from SMALLINT to MEDIUMINT', '2017-06-02');"
}
function downgrade_from_22(){
    # echo "    downgrade database from version 0.22 to version 0.21"
    echo "      Changed type of ram in 'flavors' from MEDIUMINT to SMALLINT"
    sql "ALTER TABLE flavors CHANGE COLUMN ram ram SMALLINT(5) UNSIGNED NULL DEFAULT NULL AFTER disk;"
    sql "DELETE FROM schema_version WHERE version_int='22';"
}

function upgrade_to_23(){
    # echo "    upgrade database from version 0.22 to version 0.23"
    echo "      add column 'availability_zone' at table 'vms'"
    sql "ALTER TABLE mano_db.vms ADD COLUMN availability_zone VARCHAR(255) NULL AFTER modified_at;"
    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) VALUES (23, '0.23', '0.5.20',"\
        "'Changed type of ram in flavors from SMALLINT to MEDIUMINT', '2017-08-29');"
}
function downgrade_from_23(){
    # echo "    downgrade database from version 0.23 to version 0.22"
    echo "      remove column 'availability_zone' from table 'vms'"
    sql "ALTER TABLE mano_db.vms DROP COLUMN availability_zone;"
    sql "DELETE FROM schema_version WHERE version_int='23';"
}

function upgrade_to_24(){
    # echo "    upgrade database from version 0.23 to version 0.24"
    echo "      Add 'count' to table 'vms'"

    sql "ALTER TABLE vms ADD COLUMN count SMALLINT NOT NULL DEFAULT '1' AFTER vnf_id;"
    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) "\
         "VALUES (24, '0.24', '0.5.21', 'Added vnfd fields', '2017-08-29');"
}
function downgrade_from_24(){
    # echo "    downgrade database from version 0.24 to version 0.23"
    echo "      Remove 'count' from table 'vms'"
    sql "ALTER TABLE vms DROP COLUMN count;"
    sql "DELETE FROM schema_version WHERE version_int='24';"
}
function upgrade_to_25(){
    # echo "    upgrade database from version 0.24 to version 0.25"
    echo "      Add 'osm_id','short_name','vendor' to tables 'vnfs', 'scenarios'"
    for table in vnfs scenarios; do
        sql "ALTER TABLE $table ADD COLUMN osm_id VARCHAR(255) NULL AFTER uuid, "\
             "ADD UNIQUE INDEX osm_id_tenant_id (osm_id, tenant_id), "\
             "ADD COLUMN short_name VARCHAR(255) NULL AFTER name, "\
             "ADD COLUMN vendor VARCHAR(255) NULL AFTER description;"
    done
    sql "ALTER TABLE vnfs ADD COLUMN mgmt_access VARCHAR(2000) NULL AFTER vendor;"
    sql "ALTER TABLE vms ADD COLUMN osm_id VARCHAR(255) NULL AFTER uuid;"
    sql "ALTER TABLE sce_vnfs ADD COLUMN member_vnf_index SMALLINT(6) NULL DEFAULT NULL AFTER uuid;"
    echo "      Add 'security_group' to table 'ip_profiles'"
    sql "ALTER TABLE ip_profiles ADD COLUMN security_group VARCHAR(255) NULL DEFAULT NULL AFTER dhcp_count;"

    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) "\
         "VALUES (25, '0.25', '0.5.22', 'Added osm_id to vnfs,scenarios', '2017-09-01');"
}
function downgrade_from_25(){
    # echo "    downgrade database from version 0.25 to version 0.24"
    echo "      Remove 'osm_id','short_name','vendor' from tables 'vnfs', 'scenarios'"
    for table in vnfs scenarios; do
        sql "ALTER TABLE $table DROP INDEX  osm_id_tenant_id, DROP COLUMN osm_id, "\
             "DROP COLUMN short_name, DROP COLUMN vendor;"
    done
    sql "ALTER TABLE vnfs DROP COLUMN mgmt_access;"
    sql "ALTER TABLE vms DROP COLUMN osm_id;"
    sql "ALTER TABLE sce_vnfs DROP COLUMN member_vnf_index;"
    echo "      Remove 'security_group' from table 'ip_profiles'"
    sql "ALTER TABLE ip_profiles DROP COLUMN security_group;"

    sql "DELETE FROM schema_version WHERE version_int='25';"
}

function upgrade_to_26(){
    echo "      Add name to table datacenter_tenants"
    sql "ALTER TABLE datacenter_tenants ADD COLUMN name VARCHAR(255) NULL AFTER uuid;"
    sql "UPDATE datacenter_tenants as dt join datacenters as d on dt.datacenter_id = d.uuid set dt.name=d.name;"
    echo "      Add 'SCHEDULED' to 'status' at tables 'instance_nets', 'instance_vms'"
    sql "ALTER TABLE instance_vms CHANGE COLUMN status status ENUM('ACTIVE:NoMgmtIP','ACTIVE','INACTIVE','BUILD',"\
         "'ERROR','VIM_ERROR','PAUSED','SUSPENDED','DELETED','SCHEDULED_CREATION','SCHEDULED_DELETION') "\
         "NOT NULL DEFAULT 'BUILD';"
    sql "ALTER TABLE instance_nets CHANGE COLUMN status status ENUM('ACTIVE','INACTIVE','DOWN','BUILD','ERROR',"\
         "'VIM_ERROR','DELETED','SCHEDULED_CREATION','SCHEDULED_DELETION') NOT NULL DEFAULT 'BUILD';"
    echo "      Enlarge pci at instance_interfaces to allow extended pci for SDN por mapping"
    sql "ALTER TABLE instance_interfaces CHANGE COLUMN pci pci VARCHAR(50) NULL DEFAULT NULL COMMENT 'PCI of the "\
        "physical port in the host' AFTER compute_node;"

    for t in flavor image; do
        echo "      Change 'datacenters_${t}s' to point to datacenter_tenant, add status, vim_info"
        sql "ALTER TABLE datacenters_${t}s ADD COLUMN datacenter_vim_id VARCHAR(36) NULL DEFAULT NULL AFTER "\
            "datacenter_id, ADD COLUMN status ENUM('ACTIVE','INACTIVE','BUILD','ERROR','VIM_ERROR','DELETED',"\
            "'SCHEDULED_CREATION','SCHEDULED_DELETION') NOT NULL DEFAULT 'BUILD' AFTER vim_id, ADD COLUMN vim_info "\
            "TEXT NULL AFTER status;"
        sql "UPDATE datacenters_${t}s as df left join datacenter_tenants as dt on dt.datacenter_id=df.datacenter_id "\
            "set df.datacenter_vim_id=dt.uuid;"
        sql "DELETE FROM datacenters_${t}s WHERE datacenter_vim_id is NULL;"
        sql "ALTER TABLE datacenters_${t}s CHANGE COLUMN datacenter_vim_id datacenter_vim_id VARCHAR(36) NOT NULL;"
        sql "ALTER TABLE datacenters_${t}s ADD CONSTRAINT FK_datacenters_${t}s_datacenter_tenants FOREIGN KEY "\
            "(datacenter_vim_id) REFERENCES datacenter_tenants (uuid) ON UPDATE CASCADE ON DELETE CASCADE;"
        sql "ALTER TABLE datacenters_${t}s DROP FOREIGN KEY FK__datacenters_${t:0:1};"
        sql "ALTER TABLE datacenters_${t}s DROP COLUMN datacenter_id;"
	done

    echo "      Decoupling 'instance_interfaces' from scenarios/vnfs to allow scale actions"
    sql "ALTER TABLE instance_interfaces CHANGE COLUMN vim_interface_id vim_interface_id VARCHAR(128) NULL DEFAULT NULL;"
    sql "ALTER TABLE instance_interfaces CHANGE COLUMN interface_id interface_id VARCHAR(36) NULL DEFAULT NULL;"
	sql "ALTER TABLE instance_interfaces DROP FOREIGN KEY FK_instance_ids"
	sql "ALTER TABLE instance_interfaces ADD CONSTRAINT FK_instance_ids FOREIGN KEY (interface_id) "\
	    "REFERENCES interfaces (uuid) ON UPDATE CASCADE ON DELETE SET NULL;"

    echo "      Decoupling 'instance_vms' from scenarios/vnfs to allow scale actions"
    sql "ALTER TABLE instance_vms CHANGE COLUMN vim_vm_id vim_vm_id VARCHAR(128) NULL DEFAULT NULL;"
    sql "ALTER TABLE instance_vms CHANGE COLUMN vm_id vm_id VARCHAR(36) NULL DEFAULT NULL;"
	sql "ALTER TABLE instance_vms DROP FOREIGN KEY FK_instance_vms_vms;"
	sql "ALTER TABLE instance_vms ADD CONSTRAINT FK_instance_vms_vms FOREIGN KEY (vm_id) "\
	    "REFERENCES vms (uuid) ON UPDATE CASCADE ON DELETE SET NULL;"

    echo "      Decoupling 'instance_nets' from scenarios/vnfs to allow scale actions"
    sql "ALTER TABLE instance_nets CHANGE COLUMN vim_net_id vim_net_id VARCHAR(128) NULL DEFAULT NULL;"

    echo "      Decoupling 'instance_scenarios' from scenarios"
    sql "ALTER TABLE instance_scenarios CHANGE COLUMN scenario_id scenario_id VARCHAR(36) NULL DEFAULT NULL;"
	sql "ALTER TABLE instance_scenarios DROP FOREIGN KEY FK_instance_scenarios_scenarios;"
	sql "ALTER TABLE instance_scenarios ADD CONSTRAINT FK_instance_scenarios_scenarios FOREIGN KEY (scenario_id) "\
	    "REFERENCES scenarios (uuid) ON UPDATE CASCADE ON DELETE SET NULL;"

    echo "      Create table instance_actions, vim_actions"
    sql "CREATE TABLE IF NOT EXISTS instance_actions (
	    uuid VARCHAR(36) NOT NULL,
	    tenant_id VARCHAR(36) NULL DEFAULT NULL,
	    instance_id VARCHAR(36) NULL DEFAULT NULL,
	    description VARCHAR(64) NULL DEFAULT NULL COMMENT 'CREATE, DELETE, SCALE OUT/IN, ...',
	    number_tasks SMALLINT(6) NOT NULL DEFAULT '1',
	    number_done SMALLINT(6) NOT NULL DEFAULT '0',
	    number_failed SMALLINT(6) NOT NULL DEFAULT '0',
	    created_at DOUBLE NOT NULL,
	    modified_at DOUBLE NULL DEFAULT NULL,
	    PRIMARY KEY (uuid),
        INDEX FK_actions_tenants (tenant_id),
    	CONSTRAINT FK_actions_tenant FOREIGN KEY (tenant_id) REFERENCES nfvo_tenants (uuid) ON UPDATE CASCADE ON DELETE CASCADE)
		COMMENT='Contains client actions over instances'
        COLLATE='utf8_general_ci'
        ENGINE=InnoDB;"  

    sql "CREATE TABLE IF NOT EXISTS vim_actions (
	    instance_action_id VARCHAR(36) NOT NULL,
	    task_index INT(6) NOT NULL,
	    datacenter_vim_id VARCHAR(36) NOT NULL,
	    vim_id VARCHAR(64) NULL DEFAULT NULL,
	    action VARCHAR(36) NOT NULL COMMENT 'CREATE,DELETE,START,STOP...',
	    item ENUM('datacenters_flavors','datacenter_images','instance_nets','instance_vms','instance_interfaces') NOT NULL COMMENT 'table where the item is stored',
	    item_id VARCHAR(36) NULL DEFAULT NULL COMMENT 'uuid of the entry in the table',
	    status ENUM('SCHEDULED', 'BUILD', 'DONE', 'FAILED', 'SUPERSEDED') NOT NULL DEFAULT 'SCHEDULED',
	    extra TEXT NULL DEFAULT NULL COMMENT 'json with params:, depends_on: for the task',
	    error_msg VARCHAR(1024) NULL DEFAULT NULL,
	    created_at DOUBLE NOT NULL,
	    modified_at DOUBLE NULL DEFAULT NULL,
	    PRIMARY KEY (task_index, instance_action_id),
        INDEX FK_actions_instance_actions (instance_action_id),
    	CONSTRAINT FK_actions_instance_actions FOREIGN KEY (instance_action_id) REFERENCES instance_actions (uuid) ON UPDATE CASCADE ON DELETE CASCADE,
        INDEX FK_actions_vims (datacenter_vim_id),
    	CONSTRAINT FK_actions_vims FOREIGN KEY (datacenter_vim_id) REFERENCES datacenter_tenants (uuid) ON UPDATE CASCADE ON DELETE CASCADE)
        COMMENT='Table with the individual VIM actions.'
        COLLATE='utf8_general_ci'
        ENGINE=InnoDB;"  

    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) "\
         "VALUES (26, '0.26', '0.5.23', 'Several changes', '2017-09-09');"
}
function downgrade_from_26(){
    echo "      Remove name from table datacenter_tenants"
    sql "ALTER TABLE datacenter_tenants DROP COLUMN name;"
    echo "      Remove 'SCHEDULED' from the 'status' at tables 'instance_nets', 'instance_vms'"
    sql "ALTER TABLE instance_vms CHANGE COLUMN status status ENUM('ACTIVE:NoMgmtIP','ACTIVE','INACTIVE','BUILD',"\
         "'ERROR','VIM_ERROR','PAUSED','SUSPENDED','DELETED') NOT NULL DEFAULT 'BUILD';"
    sql "ALTER TABLE instance_nets CHANGE COLUMN status status ENUM('ACTIVE','DOWN','BUILD','ERROR','VIM_ERROR',"\
         "'INACTIVE','DELETED') NOT NULL DEFAULT 'BUILD';"
    echo "      Shorten back pci at instance_interfaces to allow extended pci for SDN por mapping"
    sql "ALTER TABLE instance_interfaces CHANGE COLUMN pci pci VARCHAR(12) NULL DEFAULT NULL COMMENT 'PCI of the "\
        "physical port in the host' AFTER compute_node;"

    for t in flavor image; do
        echo "      Restore back 'datacenters_${t}s'"
        sql "ALTER TABLE datacenters_${t}s ADD COLUMN datacenter_id VARCHAR(36) NULL DEFAULT NULL AFTER "\
            "${t}_id, DROP COLUMN status, DROP COLUMN vim_info ;"
        sql "UPDATE datacenters_${t}s as df left join datacenter_tenants as dt on dt.uuid=df.datacenter_vim_id set "\
            "df.datacenter_id=dt.datacenter_id;"
        sql "ALTER TABLE datacenters_${t}s CHANGE COLUMN datacenter_id datacenter_id VARCHAR(36) NOT NULL;"
        sql "ALTER TABLE datacenters_${t}s ADD CONSTRAINT FK__datacenters_${t:0:1} FOREIGN KEY "\
            "(datacenter_id) REFERENCES datacenters (uuid), DROP FOREIGN KEY FK_datacenters_${t}s_datacenter_tenants, "\
            "DROP COLUMN datacenter_vim_id;"
    done

    echo "      Restore back 'instance_interfaces' coupling to scenarios/vnfs"
    sql "ALTER TABLE instance_interfaces CHANGE COLUMN vim_interface_id vim_interface_id VARCHAR(36) NULL DEFAULT NULL;"
	sql "ALTER TABLE instance_interfaces DROP FOREIGN KEY FK_instance_ids"
    sql "ALTER TABLE instance_interfaces CHANGE COLUMN interface_id interface_id VARCHAR(36) NOT NULL;"
	sql "ALTER TABLE instance_interfaces ADD CONSTRAINT FK_instance_ids FOREIGN KEY (interface_id) "\
	    "REFERENCES interfaces (uuid);"

    echo "      Restore back 'instance_vms' coupling to scenarios/vnfs"
    echo "      Decoupling 'instance vms' from scenarios/vnfs to allow scale actions"
    sql "UPDATE instance_vms SET vim_vm_id='' WHERE vim_vm_id is NULL;"
    sql "ALTER TABLE instance_vms CHANGE COLUMN vim_vm_id vim_vm_id VARCHAR(36) NOT NULL;"
	sql "ALTER TABLE instance_vms DROP FOREIGN KEY FK_instance_vms_vms;"
    sql "ALTER TABLE instance_vms CHANGE COLUMN vm_id vm_id VARCHAR(36) NOT NULL;"
	sql "ALTER TABLE instance_vms ADD CONSTRAINT FK_instance_vms_vms FOREIGN KEY (vm_id) "\
	    "REFERENCES vms (uuid);"

    echo "      Restore back 'instance_nets' coupling to scenarios/vnfs"
    sql "UPDATE instance_nets SET vim_net_id='' WHERE vim_net_id is NULL;"
    sql "ALTER TABLE instance_nets CHANGE COLUMN vim_net_id vim_net_id VARCHAR(36) NOT NULL;"

    echo "      Restore back  'instance_scenarios' coupling to scenarios"
	sql "ALTER TABLE instance_scenarios DROP FOREIGN KEY FK_instance_scenarios_scenarios;"
    sql "ALTER TABLE instance_scenarios CHANGE COLUMN scenario_id scenario_id VARCHAR(36) NOT NULL;"
	sql "ALTER TABLE instance_scenarios ADD CONSTRAINT FK_instance_scenarios_scenarios FOREIGN KEY (scenario_id) "\
	    "REFERENCES scenarios (uuid);"

    echo "      Delete table instance_actions"
    sql "DROP TABLE vim_actions"
    sql "DROP TABLE instance_actions"
    sql "DELETE FROM schema_version WHERE version_int='26';"
}

function upgrade_to_27(){
    echo "      Added 'encrypted_RO_priv_key','RO_pub_key' to table 'nfvo_tenants'"
    sql "ALTER TABLE nfvo_tenants ADD COLUMN encrypted_RO_priv_key VARCHAR(2000) NULL AFTER description;"
    sql "ALTER TABLE nfvo_tenants ADD COLUMN RO_pub_key VARCHAR(510) NULL AFTER encrypted_RO_priv_key;"

    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) "\
         "VALUES (27, '0.27', '0.5.25', 'Added encrypted_RO_priv_key,RO_pub_key to table nfvo_tenants', '2017-09-29');"
}
function downgrade_from_27(){
    echo "      Remove 'encrypted_RO_priv_key','RO_pub_key' from table 'nfvo_tenants'"
    sql "ALTER TABLE nfvo_tenants DROP COLUMN encrypted_RO_priv_key;"
    sql "ALTER TABLE nfvo_tenants DROP COLUMN RO_pub_key;"
    sql "DELETE FROM schema_version WHERE version_int='27';"
}
function upgrade_to_28(){
    echo "      [Adding necessary tables for VNFFG]"
    echo "      Adding sce_vnffgs"
    sql "CREATE TABLE IF NOT EXISTS sce_vnffgs (
            uuid VARCHAR(36) NOT NULL,
            tenant_id VARCHAR(36) NULL DEFAULT NULL,
            name VARCHAR(255) NOT NULL,
            description VARCHAR(255) NULL DEFAULT NULL,
            vendor VARCHAR(255) NULL DEFAULT NULL,
            scenario_id VARCHAR(36) NOT NULL,
            created_at DOUBLE NOT NULL,
            modified_at DOUBLE NULL DEFAULT NULL,
        PRIMARY KEY (uuid),
        INDEX FK_scenarios_sce_vnffg (scenario_id),
        CONSTRAINT FK_scenarios_vnffg FOREIGN KEY (tenant_id) REFERENCES scenarios (uuid) ON UPDATE CASCADE ON DELETE CASCADE)
        COLLATE='utf8_general_ci'
        ENGINE=InnoDB;"
    echo "      Adding sce_rsps"
    sql "CREATE TABLE IF NOT EXISTS sce_rsps (
            uuid VARCHAR(36) NOT NULL,
            tenant_id VARCHAR(36) NULL DEFAULT NULL,
            name VARCHAR(255) NOT NULL,
            sce_vnffg_id VARCHAR(36) NOT NULL,
            created_at DOUBLE NOT NULL,
            modified_at DOUBLE NULL DEFAULT NULL,
        PRIMARY KEY (uuid),
        INDEX FK_sce_vnffgs_rsp (sce_vnffg_id),
        CONSTRAINT FK_sce_vnffgs_rsp FOREIGN KEY (sce_vnffg_id) REFERENCES sce_vnffgs (uuid) ON UPDATE CASCADE ON DELETE CASCADE)
        COLLATE='utf8_general_ci'
        ENGINE=InnoDB;"
    echo "      Adding sce_rsp_hops"
    sql "CREATE TABLE IF NOT EXISTS sce_rsp_hops (
            uuid VARCHAR(36) NOT NULL,
            if_order INT DEFAULT 0 NOT NULL,
            interface_id VARCHAR(36) NOT NULL,
            sce_vnf_id VARCHAR(36) NOT NULL,
            sce_rsp_id VARCHAR(36) NOT NULL,
            created_at DOUBLE NOT NULL,
            modified_at DOUBLE NULL DEFAULT NULL,
        PRIMARY KEY (uuid),
        INDEX FK_interfaces_rsp_hop (interface_id),
        INDEX FK_sce_vnfs_rsp_hop (sce_vnf_id),
        INDEX FK_sce_rsps_rsp_hop (sce_rsp_id),
        CONSTRAINT FK_interfaces_rsp_hop FOREIGN KEY (interface_id) REFERENCES interfaces (uuid) ON UPDATE CASCADE ON DELETE CASCADE,
        CONSTRAINT FK_sce_vnfs_rsp_hop FOREIGN KEY (sce_vnf_id) REFERENCES sce_vnfs (uuid) ON UPDATE CASCADE ON DELETE CASCADE,
        CONSTRAINT FK_sce_rsps_rsp_hop FOREIGN KEY (sce_rsp_id) REFERENCES sce_rsps (uuid) ON UPDATE CASCADE ON DELETE CASCADE)
        COLLATE='utf8_general_ci'
        ENGINE=InnoDB;"
    echo "      Adding sce_classifiers"
    sql "CREATE TABLE IF NOT EXISTS sce_classifiers (
            uuid VARCHAR(36) NOT NULL,
            tenant_id VARCHAR(36) NULL DEFAULT NULL,
            name VARCHAR(255) NOT NULL,
            sce_vnffg_id VARCHAR(36) NOT NULL,
            sce_rsp_id VARCHAR(36) NOT NULL,
            sce_vnf_id VARCHAR(36) NOT NULL,
            interface_id VARCHAR(36) NOT NULL,
            created_at DOUBLE NOT NULL,
            modified_at DOUBLE NULL DEFAULT NULL,
        PRIMARY KEY (uuid),
        INDEX FK_sce_vnffgs_classifier (sce_vnffg_id),
        INDEX FK_sce_rsps_classifier (sce_rsp_id),
        INDEX FK_sce_vnfs_classifier (sce_vnf_id),
        INDEX FK_interfaces_classifier (interface_id),
        CONSTRAINT FK_sce_vnffgs_classifier FOREIGN KEY (sce_vnffg_id) REFERENCES sce_vnffgs (uuid) ON UPDATE CASCADE ON DELETE CASCADE,
        CONSTRAINT FK_sce_rsps_classifier FOREIGN KEY (sce_rsp_id) REFERENCES sce_rsps (uuid) ON UPDATE CASCADE ON DELETE CASCADE,
        CONSTRAINT FK_sce_vnfs_classifier FOREIGN KEY (sce_vnf_id) REFERENCES sce_vnfs (uuid) ON UPDATE CASCADE ON DELETE CASCADE,
        CONSTRAINT FK_interfaces_classifier FOREIGN KEY (interface_id) REFERENCES interfaces (uuid) ON UPDATE CASCADE ON DELETE CASCADE)
        COLLATE='utf8_general_ci'
        ENGINE=InnoDB;"
    echo "      Adding sce_classifier_matches"
    sql "CREATE TABLE IF NOT EXISTS sce_classifier_matches (
            uuid VARCHAR(36) NOT NULL,
            ip_proto VARCHAR(2) NOT NULL,
            source_ip VARCHAR(16) NOT NULL,
            destination_ip VARCHAR(16) NOT NULL,
            source_port VARCHAR(5) NOT NULL,
            destination_port VARCHAR(5) NOT NULL,
            sce_classifier_id VARCHAR(36) NOT NULL,
            created_at DOUBLE NOT NULL,
            modified_at DOUBLE NULL DEFAULT NULL,
        PRIMARY KEY (uuid),
        INDEX FK_classifiers_classifier_match (sce_classifier_id),
        CONSTRAINT FK_sce_classifiers_classifier_match FOREIGN KEY (sce_classifier_id) REFERENCES sce_classifiers (uuid) ON UPDATE CASCADE ON DELETE CASCADE)
        COLLATE='utf8_general_ci'
        ENGINE=InnoDB;"

    echo "      [Adding necessary tables for VNFFG-SFC instance mapping]"
    echo "      Adding instance_sfis"
    sql "CREATE TABLE IF NOT EXISTS instance_sfis (
          uuid varchar(36) NOT NULL,
          instance_scenario_id varchar(36) NOT NULL,
          vim_sfi_id varchar(36) DEFAULT NULL,
          sce_rsp_hop_id varchar(36) DEFAULT NULL,
          datacenter_id varchar(36) DEFAULT NULL,
          datacenter_tenant_id varchar(36) DEFAULT NULL,
          status enum('ACTIVE','INACTIVE','BUILD','ERROR','VIM_ERROR','PAUSED','SUSPENDED','DELETED','SCHEDULED_CREATION','SCHEDULED_DELETION') NOT NULL DEFAULT 'BUILD',
          error_msg varchar(1024) DEFAULT NULL,
          vim_info text,
          created_at double NOT NULL,
          modified_at double DEFAULT NULL,
          PRIMARY KEY (uuid),
      KEY FK_instance_sfis_instance_scenarios (instance_scenario_id),
      KEY FK_instance_sfis_sce_rsp_hops (sce_rsp_hop_id),
      KEY FK_instance_sfis_datacenters (datacenter_id),
      KEY FK_instance_sfis_datacenter_tenants (datacenter_tenant_id),
      CONSTRAINT FK_instance_sfis_datacenter_tenants FOREIGN KEY (datacenter_tenant_id) REFERENCES datacenter_tenants (uuid),
      CONSTRAINT FK_instance_sfis_datacenters FOREIGN KEY (datacenter_id) REFERENCES datacenters (uuid),
      CONSTRAINT FK_instance_sfis_instance_scenarios FOREIGN KEY (instance_scenario_id) REFERENCES instance_scenarios (uuid) ON DELETE CASCADE ON UPDATE CASCADE,
      CONSTRAINT FK_instance_sfis_sce_rsp_hops FOREIGN KEY (sce_rsp_hop_id) REFERENCES sce_rsp_hops (uuid) ON DELETE SET NULL ON UPDATE CASCADE)
      COLLATE='utf8_general_ci'
      ENGINE=InnoDB;"
    echo "      Adding instance_sfs"
    sql "CREATE TABLE IF NOT EXISTS instance_sfs (
          uuid varchar(36) NOT NULL,
          instance_scenario_id varchar(36) NOT NULL,
          vim_sf_id varchar(36) DEFAULT NULL,
          sce_rsp_hop_id varchar(36) DEFAULT NULL,
          datacenter_id varchar(36) DEFAULT NULL,
          datacenter_tenant_id varchar(36) DEFAULT NULL,
          status enum('ACTIVE','INACTIVE','BUILD','ERROR','VIM_ERROR','PAUSED','SUSPENDED','DELETED','SCHEDULED_CREATION','SCHEDULED_DELETION') NOT NULL DEFAULT 'BUILD',
          error_msg varchar(1024) DEFAULT NULL,
          vim_info text,
          created_at double NOT NULL,
          modified_at double DEFAULT NULL,
      PRIMARY KEY (uuid),
      KEY FK_instance_sfs_instance_scenarios (instance_scenario_id),
      KEY FK_instance_sfs_sce_rsp_hops (sce_rsp_hop_id),
      KEY FK_instance_sfs_datacenters (datacenter_id),
      KEY FK_instance_sfs_datacenter_tenants (datacenter_tenant_id),
      CONSTRAINT FK_instance_sfs_datacenter_tenants FOREIGN KEY (datacenter_tenant_id) REFERENCES datacenter_tenants (uuid),
      CONSTRAINT FK_instance_sfs_datacenters FOREIGN KEY (datacenter_id) REFERENCES datacenters (uuid),
      CONSTRAINT FK_instance_sfs_instance_scenarios FOREIGN KEY (instance_scenario_id) REFERENCES instance_scenarios (uuid) ON DELETE CASCADE ON UPDATE CASCADE,
      CONSTRAINT FK_instance_sfs_sce_rsp_hops FOREIGN KEY (sce_rsp_hop_id) REFERENCES sce_rsp_hops (uuid) ON DELETE SET NULL ON UPDATE CASCADE)
      COLLATE='utf8_general_ci'
      ENGINE=InnoDB;"
    echo "      Adding instance_classifications"
    sql "CREATE TABLE IF NOT EXISTS instance_classifications (
          uuid varchar(36) NOT NULL,
          instance_scenario_id varchar(36) NOT NULL,
          vim_classification_id varchar(36) DEFAULT NULL,
          sce_classifier_match_id varchar(36) DEFAULT NULL,
          datacenter_id varchar(36) DEFAULT NULL,
          datacenter_tenant_id varchar(36) DEFAULT NULL,
          status enum('ACTIVE','INACTIVE','BUILD','ERROR','VIM_ERROR','PAUSED','SUSPENDED','DELETED','SCHEDULED_CREATION','SCHEDULED_DELETION') NOT NULL DEFAULT 'BUILD',
          error_msg varchar(1024) DEFAULT NULL,
          vim_info text,
          created_at double NOT NULL,
          modified_at double DEFAULT NULL,
      PRIMARY KEY (uuid),
      KEY FK_instance_classifications_instance_scenarios (instance_scenario_id),
      KEY FK_instance_classifications_sce_classifier_matches (sce_classifier_match_id),
      KEY FK_instance_classifications_datacenters (datacenter_id),
      KEY FK_instance_classifications_datacenter_tenants (datacenter_tenant_id),
      CONSTRAINT FK_instance_classifications_datacenter_tenants FOREIGN KEY (datacenter_tenant_id) REFERENCES datacenter_tenants (uuid),
      CONSTRAINT FK_instance_classifications_datacenters FOREIGN KEY (datacenter_id) REFERENCES datacenters (uuid),
      CONSTRAINT FK_instance_classifications_instance_scenarios FOREIGN KEY (instance_scenario_id) REFERENCES instance_scenarios (uuid) ON DELETE CASCADE ON UPDATE CASCADE,
      CONSTRAINT FK_instance_classifications_sce_classifier_matches FOREIGN KEY (sce_classifier_match_id) REFERENCES sce_classifier_matches (uuid) ON DELETE SET NULL ON UPDATE CASCADE)
      COLLATE='utf8_general_ci'
      ENGINE=InnoDB;"
    echo "      Adding instance_sfps"
    sql "CREATE TABLE IF NOT EXISTS instance_sfps (
          uuid varchar(36) NOT NULL,
          instance_scenario_id varchar(36) NOT NULL,
          vim_sfp_id varchar(36) DEFAULT NULL,
          sce_rsp_id varchar(36) DEFAULT NULL,
          datacenter_id varchar(36) DEFAULT NULL,
          datacenter_tenant_id varchar(36) DEFAULT NULL,
          status enum('ACTIVE','INACTIVE','BUILD','ERROR','VIM_ERROR','PAUSED','SUSPENDED','DELETED','SCHEDULED_CREATION','SCHEDULED_DELETION') NOT NULL DEFAULT 'BUILD',
          error_msg varchar(1024) DEFAULT NULL,
          vim_info text,
          created_at double NOT NULL,
          modified_at double DEFAULT NULL,
      PRIMARY KEY (uuid),
      KEY FK_instance_sfps_instance_scenarios (instance_scenario_id),
      KEY FK_instance_sfps_sce_rsps (sce_rsp_id),
      KEY FK_instance_sfps_datacenters (datacenter_id),
      KEY FK_instance_sfps_datacenter_tenants (datacenter_tenant_id),
      CONSTRAINT FK_instance_sfps_datacenter_tenants FOREIGN KEY (datacenter_tenant_id) REFERENCES datacenter_tenants (uuid),
      CONSTRAINT FK_instance_sfps_datacenters FOREIGN KEY (datacenter_id) REFERENCES datacenters (uuid),
      CONSTRAINT FK_instance_sfps_instance_scenarios FOREIGN KEY (instance_scenario_id) REFERENCES instance_scenarios (uuid) ON DELETE CASCADE ON UPDATE CASCADE,
      CONSTRAINT FK_instance_sfps_sce_rsps FOREIGN KEY (sce_rsp_id) REFERENCES sce_rsps (uuid) ON DELETE SET NULL ON UPDATE CASCADE)
      COLLATE='utf8_general_ci'
      ENGINE=InnoDB;"


    echo "      [Altering vim_actions table]"
    sql "ALTER TABLE vim_actions MODIFY COLUMN item ENUM('datacenters_flavors','datacenter_images','instance_nets','instance_vms','instance_interfaces','instance_sfis','instance_sfs','instance_classifications','instance_sfps') NOT NULL COMMENT 'table where the item is stored'"

    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) "\
         "VALUES (28, '0.28', '0.5.28', 'Adding VNFFG-related tables', '2017-11-20');"
}
function downgrade_from_28(){
    echo "      [Undo adding the VNFFG tables]"
    echo "      Dropping instance_sfps"
    sql "DROP TABLE instance_sfps;"
    echo "      Dropping sce_classifications"
    sql "DROP TABLE instance_classifications;"
    echo "      Dropping instance_sfs"
    sql "DROP TABLE instance_sfs;"
    echo "      Dropping instance_sfis"
    sql "DROP TABLE instance_sfis;"
    echo "      Dropping sce_classifier_matches"
    echo "      [Undo adding the VNFFG-SFC instance mapping tables]"
    sql "DROP TABLE sce_classifier_matches;"
    echo "      Dropping sce_classifiers"
    sql "DROP TABLE sce_classifiers;"
    echo "      Dropping sce_rsp_hops"
    sql "DROP TABLE sce_rsp_hops;"
    echo "      Dropping sce_rsps"
    sql "DROP TABLE sce_rsps;"
    echo "      Dropping sce_vnffgs"
    sql "DROP TABLE sce_vnffgs;"
    echo "      [Altering vim_actions table]"
    sql "ALTER TABLE vim_actions MODIFY COLUMN item ENUM('datacenters_flavors','datacenter_images','instance_nets','instance_vms','instance_interfaces') NOT NULL COMMENT 'table where the item is stored'"
    sql "DELETE FROM schema_version WHERE version_int='28';"
}
function upgrade_to_29(){
    echo "      Change 'member_vnf_index' from int to str at 'sce_vnfs'"
    sql "ALTER TABLE sce_vnfs CHANGE COLUMN member_vnf_index member_vnf_index VARCHAR(255) NULL DEFAULT NULL AFTER uuid;"
    echo "      Add osm_id to 'nets's and 'sce_nets'"
    sql "ALTER TABLE nets ADD COLUMN osm_id VARCHAR(255) NULL AFTER uuid;"
    sql "ALTER TABLE sce_nets ADD COLUMN osm_id VARCHAR(255) NULL AFTER uuid;"
    sql "INSERT INTO schema_version (version_int, version, openmano_ver, comments, date) "\
         "VALUES (29, '0.29', '0.5.59', 'Change member_vnf_index to str accordingly to the model', '2018-04-11');"
}
function downgrade_from_29(){
    echo "      Change back 'member_vnf_index' from str to int at 'sce_vnfs'"
    sql "ALTER TABLE sce_vnfs CHANGE COLUMN member_vnf_index member_vnf_index SMALLINT NULL DEFAULT NULL AFTER uuid;"
    echo "      Remove osm_id from 'nets's and 'sce_nets'"
    sql "ALTER TABLE nets DROP COLUMN osm_id;"
    sql "ALTER TABLE sce_nets DROP COLUMN osm_id;"
    sql "DELETE FROM schema_version WHERE version_int='29';"
}
function upgrade_to_X(){
    echo "      change 'datacenter_nets'"
    sql "ALTER TABLE datacenter_nets ADD COLUMN vim_tenant_id VARCHAR(36) NOT NULL AFTER datacenter_id, DROP INDEX name_datacenter_id, ADD UNIQUE INDEX name_datacenter_id (name, datacenter_id, vim_tenant_id);"
}
function downgrade_from_X(){
    echo "      Change back 'datacenter_nets'"
    sql "ALTER TABLE datacenter_nets DROP COLUMN vim_tenant_id, DROP INDEX name_datacenter_id, ADD UNIQUE INDEX name_datacenter_id (name, datacenter_id);"
}
#TODO ... put functions here

# echo "db version = "${DATABASE_VER_NUM}
[ $DB_VERSION -eq $DATABASE_VER_NUM ] && echo "    current database version '$DATABASE_VER_NUM' is ok" && exit 0

# Create a backup database content
TEMPFILE2="$(mktemp -q --tmpdir "backupdb.XXXXXX.sql")"
trap 'rm -f "$TEMPFILE2"' EXIT
mysqldump $DEF_EXTRA_FILE_PARAM --add-drop-table --add-drop-database --routines --databases $DBNAME > $TEMPFILE2

function rollback_db()
{
    cat $TEMPFILE2 | mysql $DEF_EXTRA_FILE_PARAM && echo "    Aborted! Rollback database OK" ||
        echo "    Aborted! Rollback database FAIL"
    exit 1
}

function sql()    # send a sql command
{
    echo "$*" | $DBCMD || ! echo "    ERROR with command '$*'" || rollback_db
    return 0
}

#UPGRADE DATABASE step by step
while [ $DB_VERSION -gt $DATABASE_VER_NUM ]
do
    echo "    upgrade database from version '$DATABASE_VER_NUM' to '$((DATABASE_VER_NUM+1))'"
    DATABASE_VER_NUM=$((DATABASE_VER_NUM+1))
    upgrade_to_${DATABASE_VER_NUM}
    #FILE_="${DIRNAME}/upgrade_to_${DATABASE_VER_NUM}.sh"
    #[ ! -x "$FILE_" ] && echo "Error, can not find script '$FILE_' to upgrade" >&2 && exit -1
    #$FILE_ || exit -1  # if fail return
done

#DOWNGRADE DATABASE step by step
while [ $DB_VERSION -lt $DATABASE_VER_NUM ]
do
    echo "    downgrade database from version '$DATABASE_VER_NUM' to '$((DATABASE_VER_NUM-1))'"
    #FILE_="${DIRNAME}/downgrade_from_${DATABASE_VER_NUM}.sh"
    #[ ! -x "$FILE_" ] && echo "Error, can not find script '$FILE_' to downgrade" >&2 && exit -1
    #$FILE_ || exit -1  # if fail return
    downgrade_from_${DATABASE_VER_NUM}
    DATABASE_VER_NUM=$((DATABASE_VER_NUM-1))
done

#echo done

