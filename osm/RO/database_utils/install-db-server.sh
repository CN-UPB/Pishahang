#!/usr/bin/env bash

DB_NAME='mano_db'
DB_ADMIN_USER="root"
DB_USER="mano"
DB_PASS="manopw"
DB_ADMIN_PASSWD=""
DB_PORT="3306"
DB_HOST=""
DB_HOST_PARAM=""
QUIET_MODE=""
FORCEDB=""
UPDATEDB=""
NO_PACKAGES=""
UNINSTALL=""


function usage(){
    echo -e "usage: sudo $0 [OPTIONS]"
    echo -e "Install openmano database server and the needed packages"
    echo -e "  OPTIONS"
    echo -e "     -U USER:    database admin user. '$DB_ADMIN_USER' by default. Prompts if needed"
    echo -e "     -P PASS:    database admin password to be used or installed. Prompts if needed"
    echo -e "     -d: database name, '$DB_NAME' by default"
    echo -e "     -u: database user, '$DB_USER' by default"
    echo -e "     -p: database pass, '$DB_PASS' by default"
    echo -e "     -H: HOST  database host. 'localhost' by default"
    echo -e "     -T: PORT  database port. '$DB_PORT' by default"
    echo -e "     -q --quiet: install in unattended mode"
    echo -e "     -h --help:  show this help"
    echo -e "     --forcedb:  if database exists, it is dropped and a new one is created"
    echo -e "     --updatedb: if database exists, it preserves the content and it is updated to the needed version"
    echo -e "     --no-install-packages: use this option to skip updating and installing the requires packages. This avoid wasting time if you are sure requires packages are present e.g. because of a previous installation"
    echo -e "     --unistall: delete database"
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

function _install_mysql_package(){
    echo '
    #################################################################
    #####               INSTALL REQUIRED PACKAGES               #####
    #################################################################'
    [ "$_DISTRO" == "Ubuntu" ] && ! install_packages "mysql-server" && exit 1
    [ "$_DISTRO" == "CentOS" -o "$_DISTRO" == "Red" ] && ! install_packages "mariadb mariadb-server" && exit 1

    if [[ "$_DISTRO" == "Ubuntu" ]]
    then
        #start services. By default CentOS does not start services
        service mysql start >> /dev/null
        # try to set admin password, ignore if fails
        [[ -n $DBPASSWD ]] && mysqladmin -u $DB_ADMIN_USER -s password $DB_ADMIN_PASSWD
    fi

    if [ "$_DISTRO" == "CentOS" -o "$_DISTRO" == "Red" ]
    then
        #start services. By default CentOS does not start services
        service mariadb start
        service httpd   start
        systemctl enable mariadb
        systemctl enable httpd
        ask_user "Do you want to configure mariadb (recommended if not done before) (Y/n)? " y &&
            mysql_secure_installation

        ask_user "Do you want to set firewall to grant web access port 80,443  (Y/n)? " y &&
            firewall-cmd --permanent --zone=public --add-service=http &&
            firewall-cmd --permanent --zone=public --add-service=https &&
            firewall-cmd --reload
    fi
}

function _create_db(){
    echo '
    #################################################################
    #####        CREATE AND INIT DATABASE                       #####
    #################################################################'
    echo "mysqladmin --defaults-extra-file="$TEMPFILE" -s create ${DB_NAME}"
    mysqladmin --defaults-extra-file="$TEMPFILE" -s create ${DB_NAME} \
        || ! echo "Error creating ${DB_NAME} database" >&2 \
        || exit 1
    echo "CREATE USER $DB_USER@'localhost' IDENTIFIED BY '$DB_PASS';"   | mysql --defaults-extra-file="$TEMPFILE" -s 2>/dev/null \
        || echo "Warning: User '$DB_USER' cannot be created at database. Probably exist" >&2
    echo "GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '$DB_USER'@'localhost';" | mysql --defaults-extra-file="$TEMPFILE" -s \
        || ! echo "Error: Granting privileges to user '$DB_USER' at database" >&2 \
        || exit 1
    echo " Database '${DB_NAME}' created, user '$DB_USER' password '$DB_PASS'"
    DIRNAME=$(dirname $(readlink -f ${BASH_SOURCE[0]}))
    ${DIRNAME}/init_mano_db.sh -u"$DB_USER" -p"$DB_PASS" -d"$DB_NAME" -P"$DB_PORT" $DB_HOST_PARAM \
        || ! echo "Error initializing database '$DB_NAME'" >&2 \
        || exit 1
}

function _delete_db(){
   mysqladmin --defaults-extra-file="$TEMPFILE" -s drop "${DB_NAME}" $DBDELETEPARAM \
       || ! echo "Error: Could not delete '${DB_NAME}' database" >&2 \
       || exit 1
}

function _update_db(){
    echo '
    #################################################################
    #####        UPDATE DATABASE                                #####
    #################################################################'
    echo "CREATE USER $DB_USER@'localhost' IDENTIFIED BY '$DB_PASS';" | mysql --defaults-extra-file="$TEMPFILE" -s 2>/dev/null \
        || echo "Warning: User '$DB_USER' cannot be created at database. Probably exist" >&2
    echo "GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '$DB_USER'@'localhost';" | mysql --defaults-extra-file="$TEMPFILE" -s \
        || ! echo "Error: Granting privileges to user '$DB_USER' at database" >&2 \
        || exit 1
    echo " Granted privileges to user '$DB_USER' password '$DB_PASS' to existing database '${DB_NAME}'"
    DIRNAME=$(dirname $(readlink -f ${BASH_SOURCE[0]}))
    ${DIRNAME}/migrate_mano_db.sh -u"$DB_USER" -p"$DB_PASS" -d"$DB_NAME" -P"$DB_PORT" $DB_HOST_PARAM \
        || ! echo "Error updating database '$DB_NAME'" >&2 \
        || exit 1
}

function _uninstall_db(){
echo '
    #################################################################
    #####        DELETE DATABASE                                #####
    #################################################################'
    DBDELETEPARAM=""
    [[ -n $QUIET_MODE ]] && DBDELETEPARAM="-f"
    _delete_db
}

function db_exists(){  # (db_name, credential_file)
    # check credentials
    mysqlshow --defaults-extra-file="$2" >/dev/null  || exit 1
    if mysqlshow --defaults-extra-file="$2" | grep -v Wildcard | grep -w -q $1
    then
        # echo " DB $1 exists"
        return 0
    fi
    # echo " DB $1 does not exist"
    return 1
}

while getopts ":U:P:d:u:p:H:T:hiq-:" o; do
    case "${o}" in
        U)
            export DB_ADMIN_USER="$OPTARG"
            ;;
        P)
            export DB_ADMIN_PASSWD="$OPTARG"
            ;;
        d)
            export DB_NAME="$OPTARG"
            ;;
        u)
            export DB_USER="$OPTARG"
            ;;
        p)
            export DB_PASS="$OPTARG"
            ;;
        H)
            export DB_HOST="$OPTARG"
            export DB_HOST_PARAM="-h$DB_HOST"
            ;;
        T)
            export DB_PORT="$OPTARG"
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
            [ "${OPTARG}" == "forcedb" ] && FORCEDB="y" && continue
            [ "${OPTARG}" == "updatedb" ] && UPDATEDB="y" && continue
            [ "${OPTARG}" == "quiet" ] && export QUIET_MODE=yes && export DEBIAN_FRONTEND=noninteractive && continue
            [ "${OPTARG}" == "no-install-packages" ] && export NO_PACKAGES=yes && continue
            [ "${OPTARG}" == "uninstall" ] &&  UNINSTALL="y" && continue
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
if [ -n "$FORCEDB" ] && [ -n "$UPDATEDB" ] ; then
    echo "Error: options --forcedb and --updatedb are mutually exclusive" >&2
    exit 1
fi

# Discover Linux distribution
# try redhat type
[ -f /etc/redhat-release ] && _DISTRO=$(cat /etc/redhat-release 2>/dev/null | cut  -d" " -f1)
# if not assuming ubuntu type
[ -f /etc/redhat-release ] || _DISTRO=$(lsb_release -is  2>/dev/null)

if [[ -z "$NO_PACKAGES" ]]
then
    [ "$USER" != "root" ] && echo "Needed root privileges" >&2 && exit 1
    _install_mysql_package || exit 1
fi

# Creating temporary file for MYSQL installation and initialization"
TEMPFILE="$(mktemp -q --tmpdir "installdb.XXXXXX")"
trap 'rm -f "$TEMPFILE"' EXIT
chmod 0600 "$TEMPFILE"
echo -e "[client]\n user='${DB_ADMIN_USER}'\n password='$DB_ADMIN_PASSWD'\n host='$DB_HOST'\n port='$DB_PORT'" > "$TEMPFILE"

#check and ask for database user password. Must be done after database installation
if [[ -z $QUIET_MODE ]]
then
    echo -e "\nCheking database connection and ask for credentials"
    # echo "mysqladmin --defaults-extra-file=$TEMPFILE -s status >/dev/null"
    while ! mysqladmin --defaults-extra-file="$TEMPFILE" -s status >/dev/null
    do
        [ -n "$logintry" ] &&  echo -e "\nInvalid database credentials!!!. Try again (Ctrl+c to abort)"
        [ -z "$logintry" ] &&  echo -e "\nProvide database credentials"
        read -e -p "database admin user? ($DB_ADMIN_USER) " DBUSER_
        [ -n "$DBUSER_" ] && DB_ADMIN_USER=$DBUSER_
        read -e -s -p "database admin password? (Enter for not using password) " DBPASSWD_
        [ -n "$DBPASSWD_" ] && DB_ADMIN_PASSWD="$DBPASSWD_"
        [ -z "$DBPASSWD_" ] && DB_ADMIN_PASSWD=""
        echo -e "[client]\n user='${DB_ADMIN_USER}'\n password='$DB_ADMIN_PASSWD'\n host='$DB_HOST'\n port='$DB_PORT'" > "$TEMPFILE"
        logintry="yes"
    done
fi

if [[ ! -z "$UNINSTALL" ]]
then
    _uninstall_db
    exit
fi

# Create or update database
if db_exists $DB_NAME $TEMPFILE ; then
    if [[ -n $FORCEDB ]] ; then
        # DBDELETEPARAM=""
        # [[ -n $QUIET_MODE ]] && DBDELETEPARAM="-f"
        DBDELETEPARAM="-f"
        _delete_db
        _create_db
    elif [[ -n $UPDATEDB ]] ; then
        _update_db
    elif [[ -z $QUIET_MODE ]] ; then
        echo "database '$DB_NAME' exist. Reinstall it?"
        if ask_user "Type 'y' to drop and reinstall existing database (content will be lost), Type 'n' to update existing database (y/N)? " n ; then
            _delete_db
            _create_db
        else
            _update_db
        fi
    else
        echo "Database '$DB_NAME' exists. Use option '--forcedb' to force the deletion of the existing one, or '--updatedb' to use existing one and update it"
        exit 1
    fi
else
    _create_db
fi

