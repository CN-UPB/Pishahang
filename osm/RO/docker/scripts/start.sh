#!/bin/bash


[ -z "$RO_DB_OVIM_HOST" ] && export RO_DB_OVIM_HOST="$RO_DB_HOST"
[ -z "$RO_DB_OVIM_ROOT_PASSWORD" ] && export RO_DB_OVIM_ROOT_PASSWORD="$RO_DB_ROOT_PASSWORD"

function is_db_created() {
    db_host=$1
    db_port=$2
    db_user=$3
    db_pswd=$4
    db_name=$5

    RESULT=`mysqlshow -h"$db_host" -P"$db_port" -u"$db_user" -p"$db_pswd" | grep -v Wildcard | grep -o $db_name`
    if [ "$RESULT" == "$db_name" ]; then

        RESULT=`mysqlshow -h"$db_host" -P"$db_port" -u"$db_user" -p"$db_pswd" "$db_name" | grep -v Wildcard | grep schema_version`
        #TODO validate version
        if [ -n "$RESULT" ]; then
            echo " DB $db_name exists and inited"
            return 0
        else
            echo " DB $db_name exists BUT not inited"
            return 1
        fi
    fi
    echo " DB $db_name does not exist"
    return 1
}

function configure(){
    #Database parameters
    #db_host:   localhost
    #db_user:   mano
    #db_passwd: manopw
    #db_name:   mano_db
    # Database ovim parameters
    #db_ovim_host:   localhost          # by default localhost
    #db_ovim_user:   mano               # DB user
    #db_ovim_passwd: manopw             # DB password
    #db_ovim_name:   mano_vim_db        # Name of the OVIM MANO DB


    sed -i "s/^db_host:.*/db_host: $RO_DB_HOST/" /etc/osm/openmanod.cfg || return 1
    sed -i "s/^db_user:.*/db_user: $RO_DB_USER/" /etc/osm/openmanod.cfg || return 1
    sed -i "s/^db_passwd:.*/db_passwd: $RO_DB_PASSWORD/" /etc/osm/openmanod.cfg || return 1
    sed -i "s/^db_name:.*/db_name: $RO_DB_NAME/" /etc/osm/openmanod.cfg || return 1
    sed -i "s/^db_ovim_host:.*/db_ovim_host: $RO_DB_OVIM_HOST/" /etc/osm/openmanod.cfg || return 1
    sed -i "s/^db_ovim_user:.*/db_ovim_user: $RO_DB_OVIM_USER/" /etc/osm/openmanod.cfg || return 1
    sed -i "s/^db_ovim_passwd:.*/db_ovim_passwd: $RO_DB_OVIM_PASSWORD/" /etc/osm/openmanod.cfg || return 1
    sed -i "s/^db_ovim_name:.*/db_ovim_name: $RO_DB_OVIM_NAME/" /etc/osm/openmanod.cfg || return 1
    return 0
}

max_attempts=120
function wait_db(){
    db_host=$1
    db_port=$2
    attempt=0
    echo "Wait until $max_attempts seconds for MySQL mano Server ${db_host}:${db_port} "
    while ! mysqladmin ping -h"$db_host" -P"$db_port" --silent; do
        #wait 120 sec
        if [ $attempt -ge $max_attempts ]; then
            echo
            echo "Can not connect to database ${db_host}:${db_port} during $max_attempts sec"
            return 1
        fi
        attempt=$[$attempt+1]
        echo -n "."
        sleep 1
    done
    return 0
}


echo "1/4 Apply config"
configure || exit 1


echo "2/4 Wait for db up"
wait_db "$RO_DB_HOST" "$RO_DB_PORT" || exit 1
[ "$RO_DB_OVIM_HOST" = "$RO_DB_HOST" ] ||  wait_db "$RO_DB_OVIM_HOST" "$RO_DB_OVIM_PORT" || exit 1


echo "3/4 Init database"
RO_PATH=`python -c 'import osm_ro; print(osm_ro.__path__[0])'`
echo "RO_PATH: $RO_PATH"
if ! is_db_created "$RO_DB_HOST" "$RO_DB_PORT" "$RO_DB_USER" "$RO_DB_PASSWORD" "$RO_DB_NAME"
then
    if [ -n "$RO_DB_ROOT_PASSWORD" ] ; then
        mysqladmin -h"$RO_DB_HOST" -uroot -p"$RO_DB_ROOT_PASSWORD" create "$RO_DB_NAME"
        echo "CREATE USER '${RO_DB_USER}'@'%' IDENTIFIED BY '${RO_DB_PASSWORD}';" |
            mysql -h"$RO_DB_HOST" -uroot -p"$RO_DB_ROOT_PASSWORD" || echo "user ${RO_DB_USER} already created?"
        echo "GRANT ALL PRIVILEGES ON ${RO_DB_NAME}.* TO '${RO_DB_USER}'@'%';" |
            mysql -h"$RO_DB_HOST" -uroot -p"$RO_DB_ROOT_PASSWORD"  || echo "user ${RO_DB_USER} already granted?"
    fi
    ${RO_PATH}/database_utils/init_mano_db.sh  -u "$RO_DB_USER" -p "$RO_DB_PASSWORD" -h "$RO_DB_HOST" \
        -P "${RO_DB_PORT}" -d "${RO_DB_NAME}" || exit 1
else
    echo "    migrage database version"
    ${RO_PATH}/database_utils/migrate_mano_db.sh -u "$RO_DB_USER" -p "$RO_DB_PASSWORD" -h "$RO_DB_HOST" \
        -P "$RO_DB_PORT" -d "$RO_DB_NAME"
fi

OVIM_PATH=`python -c 'import lib_osm_openvim; print(lib_osm_openvim.__path__[0])'`
echo "OVIM_PATH: $OVIM_PATH"
if ! is_db_created "$RO_DB_OVIM_HOST" "$RO_DB_OVIM_PORT" "$RO_DB_OVIM_USER" "$RO_DB_OVIM_PASSWORD" "$RO_DB_OVIM_NAME"
then
    if [ -n "$RO_DB_OVIM_ROOT_PASSWORD" ] ; then
        mysqladmin -h"$RO_DB_OVIM_HOST" -uroot -p"$RO_DB_OVIM_ROOT_PASSWORD" create "$RO_DB_OVIM_NAME"
        echo "CREATE USER '${RO_DB_OVIM_USER}'@'%' IDENTIFIED BY '${RO_DB_OVIM_PASSWORD}';" |
            mysql -h"$RO_DB_OVIM_HOST" -uroot -p"$RO_DB_OVIM_ROOT_PASSWORD" ||
            echo "user ${RO_DB_OVIM_USER} already created?"
        echo "GRANT ALL PRIVILEGES ON ${RO_DB_OVIM_NAME}.* TO '${RO_DB_OVIM_USER}'@'%';" |
            mysql -h"$RO_DB_OVIM_HOST" -uroot -p"$RO_DB_OVIM_ROOT_PASSWORD"  ||
            echo "user ${RO_DB_OVIM_USER} already granted?"
    fi
    ${OVIM_PATH}/database_utils/init_vim_db.sh  -u "$RO_DB_OVIM_USER" -p "$RO_DB_OVIM_PASSWORD" -h "$RO_DB_OVIM_HOST" \
        -P "${RO_DB_OVIM_PORT}" -d "${RO_DB_OVIM_NAME}" || exit 1
else
    echo "    migrage database version"
    ${OVIM_PATH}/database_utils/migrate_vim_db.sh -u "$RO_DB_OVIM_USER" -p "$RO_DB_OVIM_PASSWORD" -h "$RO_DB_OVIM_HOST"\
        -P "$RO_DB_OVIM_PORT" -d "$RO_DB_OVIM_NAME"
fi


echo "4/4 Try to start"
/usr/bin/openmanod -c /etc/osm/openmanod.cfg --log-file=/var/log/osm/openmano.log --create-tenant=osm
