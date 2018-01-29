#!/bin/bash

# Keycloak master administrator
KEYCLOAK_USER=${1:-admin}
KEYCLOAK_PASSWORD=${2:-admin}

# SONATA default admin
SONATA_USER=${3:-sonata}
SONATA_PASSWORD=${4:-sonata}
SONATA_EMAIL=${5:-sonata.admin@email.com}

KEYCLOAK_PORT=5601
KEYCLOAK_URL=http://localhost:$KEYCLOAK_PORT
KEYCLOAK_OPENID_TOKEN_ENDPOINT=$KEYCLOAK_URL/auth/realms/sonata/protocol/openid-connect/token
ADAPTER_URL=http://son-gtkusr:5600/api/v1/config
ADAPTER_ADMIN=http://son-gtkusr:5600/admin
KCADMIN_SCRIPT=/opt/jboss/keycloak/bin/kcadm.sh

SONATA_REALM=sonata
ADAPTER_CLIENT=adapter

# SONATA default realm-admin registration JSON object
admin_reg_data() {
    cat << EOF
{"username": "$SONATA_USER",
 "enabled": true,
 "totp": false,
 "emailVerified": false,
 "firstName": "Admin",
 "lastName": "Default",
 "email": "$SONATA_EMAIL",
 "credentials": [{"type": "password","value": "$SONATA_PASSWORD"}],
 "requiredActions": [],
 "federatedIdentities": [],
 "attributes": {"userType": ["admin"]},
 "realmRoles": [],
 "clientRoles": {},
 "groups": []
}
EOF
}

# SONATA Demo user registration JSON object, remove before using in production
demo_reg_data() {
    cat << EOF
{"username": "demo",
 "enabled": true,
 "totp": false,
 "emailVerified": false,
 "firstName": "Demo",
 "lastName": "User",
 "email": "demo.user@email.com",
 "credentials": [{"type": "password","value": "demo"}],
 "requiredActions": [],
 "federatedIdentities": [],
 "attributes": {"userType": ["developer","customer"]},
 "realmRoles": [],
 "clientRoles": {},
 "groups": []}
EOF
}

# Param: $1 = realm name
function create_realm() {
	$KCADMIN_SCRIPT create realms -s realm=$1 -s enabled=true -s sslRequired=none -i > /dev/null
	ret=$?
	if [ $ret -eq 0 ]; then
        	echo "Created realm [$1]"
	fi
	return $ret
}

# Param: $1 = realm name
function update_realm() {
    $KCADMIN_SCRIPT update realms/$1 -s accessTokenLifespan=1200 -i > /dev/null
	ret=$?
	if [ $ret -eq 0 ]; then
        	echo "Updated realm [$1] token lifespan"
	fi
	return $ret
}

# Params: $1 = realm, $2 = client name, $3 = redirect URI
function create_client() {
	cid=$($KCADMIN_SCRIPT create clients -r $1 -s clientId=$2 -s "redirectUris=[\"$3\"]" -s serviceAccountsEnabled=true -s authorizationServicesEnabled=true -s directAccessGrantsEnabled=true -i)
	ret=$?
	if [ $ret -eq 0 ]; then
        	echo "Created client [$2] for realm [$1] id=$cid"
		# /opt/jboss/keycloak/bin/kcadm.sh update clients/$cid -r sonata -s serviceAccountsEnabled=true -s authorizationServicesEnabled=true
	fi
	return $ret
}

# Params: $1 = realm, $2 = role name, $3 = role description
function create_realm_role() {
	$KCADMIN_SCRIPT create roles -r $1 -s name=$2 -s description="$3" -i > /dev/null
	ret=$?
	if [ $ret -eq 0 ]; then
        	echo "Created role [$2] for realm [$1]"
	fi
	return $ret
}

# Params: $1 = realm, $2 = role name , $3 = client-role client id , $4 = role name
function update_realm_role() {
	$KCADMIN_SCRIPT add-roles -r $1 --rname $2 --cclientid $3 --rolename $4 -i > /dev/null
	ret=$?
	if [ $ret -eq 0 ]; then
        	echo "Updated role [$2] for realm [$1]"
	fi
	return $ret
}

# Param: $1 = realm, $2 = group name
function create_group() {
	$KCADMIN_SCRIPT create groups -r $1 -s name=$2 -s $3 -i > /dev/null
	ret=$?
	if [ $ret -eq 0 ]; then
        	echo "Created group [$2] for realm [$1]"
	fi
	return $ret
}

# Params: $1 = realm, $2 = client id
function get_client_secret() {
# Attempt to retrieve the client secret
        secret=$($KCADMIN_SCRIPT get clients/$2/installation/providers/keycloak-oidc-keycloak-json -r $1 | grep secret | sed 's/"//g' | awk '{print $3}' 2>/dev/null)
        ret=$?
        if [ $ret -eq 0 ]; then
        	echo "$secret"
        fi
	return $ret
}

# Params: $1 = realm
function get_current_clients() {
# List existing clients

        clients=$($KCADMIN_SCRIPT get clients -r $1 --fields id,clientId 2>/dev/null)
        ret=$?
        if [ $ret -eq 0 ]; then
        	echo "$clients"
        fi
	return $ret
}

echo
echo "------------------------------------------------------------------------"
echo "*** Verifying if Keycloak server is up and listening on $KEYCLOAK_URL"
retries=0
until [ $(curl --connect-timeout 15 --max-time 15 -k -s -o /dev/null -I -w "%{http_code}" $KEYCLOAK_URL) -eq 200 ]; do
    	#printf '.'
    	sleep 20
    	let retries="$retries+1"
    	if [ $retries -eq 12 ]; then
		echo "Timeout waiting for Keycloak on $KEYCLOAK_URL"
		exit 1
	fi
done

echo "Keycloak server detected! Creating predefined entities..."

# Log in to create session:
$KCADMIN_SCRIPT config credentials --server $KEYCLOAK_URL/auth --realm master --user $KEYCLOAK_USER --password $KEYCLOAK_PASSWORD -o

if [ $? -ne 0 ]; then
	echo "Unable to login as admin"
	exit 1
fi

# Creating the Service Platform realm:
create_realm $SONATA_REALM

# Increase access token lifespan
echo "Increasing Access Token Lifespan to 1200"
$KCADMIN_SCRIPT update realms/$SONATA_REALM -s accessTokenLifespan=1200

# Creating the Service Platform adapter client:
create_client_out=$(create_client $SONATA_REALM $ADAPTER_CLIENT "http://son-gtkusr:5600/")
echo $create_client_out

# Listing clients
client_list=$(get_current_clients $SONATA_REALM)
echo "client_list=$client_list"

client_list0=$(echo $client_list | awk '{print $0}' | python -mjson.tool | awk '/"id"/' | awk -F ':[ \t]*' '{print $2}' | sed 's/,//g' | sed 's/"//g' )
client_list1=$(echo $client_list | awk '{print $0}' | python -mjson.tool | awk '/"clientId"/' | awk -F ':[ \t]*' '{print $2}' | sed 's/,//g' | sed 's/"//g' )

echo $client_list0
echo $client_list1

count=1
LINES=`echo $client_list1`
for LINE in $LINES ; do
    if [ "$LINE" == "$ADAPTER_CLIENT" ]; then
        echo "$count"
        echo $LINE
        adapter_cid=$(echo $client_list0 |  awk -v var=$count '{ print $var }') #awk '{print $1}')
        # awk -v var="$count" -F' ' '{ print var }'
        echo $adapter_cid
    fi
    (( count++ ))
done

# adapter_cid=$(echo $create_client_out | awk -F id= '{print $2}')
echo "adapter_cid=$adapter_cid"

# Creating predefined realm roles:
create_realm_role $SONATA_REALM son-gkeeper "\${role_access-catalogue},\${role_access-repositories}"
create_realm_role $SONATA_REALM son-catalogue ""
create_realm_role $SONATA_REALM son-repositories "\${role_read-catalogue}"
create_realm_role $SONATA_REALM son-monitor "\${role_read-catalogue},\${role_read-repositories}"
create_realm_role $SONATA_REALM son-slm "\${role_read-catalogue}"
create_realm_role $SONATA_REALM customer "\${role_read-repositories},\${role_write-repositories},\${role_execute-catalogue},\${role_read-monitoring}"
create_realm_role $SONATA_REALM developer "\${role_read-catalogue},\${role_write-catalogue},\${role_read-monitoring}"
create_realm_role $SONATA_REALM admin "\${role_realm-admin}"

# Update 'admin' role to composite-role type with 'realm-admin' role
echo Adding realm-admin role to admin role...
$KCADMIN_SCRIPT add-roles -r $SONATA_REALM --rname admin --cclientid realm-management --rolename realm-admin
# kcadm.sh add-roles -r sonata --rname admin --cclientid realm-management --rolename realm-admin
# update_realm_role $SONATA_REALM admin realm-management realm-admin

# Creating predefined realm groups where $1=realm_name $2=group_name $3=associated_role_name:
create_group $SONATA_REALM developers 'attributes.roles=["developer"]'
create_group $SONATA_REALM customers 'attributes.roles=["customer"]'
create_group $SONATA_REALM admins 'attributes.roles=["admin"]'

# Capture the adapter client secret for the next set of operations
adapter_secret=$(get_client_secret $SONATA_REALM $adapter_cid)

# Add the realm-admin role to the service account associated with the adapter client
echo Adding realm-admin role to adapter service account...
$KCADMIN_SCRIPT add-roles -r $SONATA_REALM --uusername service-account-$ADAPTER_CLIENT --cclientid realm-management --rolename realm-admin

# Attempt to get access and ID tokens. This serves two purposes:
# 1. it tests the endpoint: we make sure that the adapter client was created correctly and we have the adapter client secret, and
# 2. it has the side effect of creating the adapter "service account" user, upon which we would like to assign roles that allow us to create users.
echo "Testing adapter client token endpoint: $KEYCLOAK_OPENID_TOKEN_ENDPOINT"
resp=$(curl -k -s -o -X POST -H "Content-Type: application/x-www-form-urlencoded" -d "grant_type=client_credentials&client_id=$ADAPTER_CLIENT&client_secret=$adapter_secret" "$KEYCLOAK_OPENID_TOKEN_ENDPOINT")
token=$(echo $resp | awk '{print $1}' | python -mjson.tool | grep "access_token" | awk -F ':[ \t]*' '{print $2}' | sed 's/,//g' | sed 's/"//g')
echo "Token data="$token
#if [ $endpoint_ret -ne 200 ]; then
#	echo "Got $endpoint_ret instead of 200 OK"
#	return 1
#fi

if [ "$ADAPTER_URL" ]; then
    echo
    echo "------------------------------------------------------------------------"
    echo "*** Waiting for adapter server is up and listening on $ADAPTER_ADMIN"
    retries=0
    until [ $(curl -X GET -o /dev/null -s -w "%{http_code}" $ADAPTER_ADMIN) -eq 200 ]; do
	sleep 20
	let retries="$retries+1"
	if [ $retries -eq 12 ]; then
	    echo "Timeout waiting for adapter on $ADAPTER_ADMIN"
	    exit 1
	fi
    done
    echo "Trying to post the secret on adapter $ADAPTER_URL"
    if [ $(curl -X POST -o /dev/null -s -w "%{http_code}" -d "secret=$adapter_secret" $ADAPTER_URL) -eq 200 ]; then
	echo "Secret of client [$ADAPTER_CLIENT] successfully POSTed to $ADAPTER_URL"
    else
	echo "Unable to POST secret to $ADAPTER_URL"
    fi
fi

sleep 3

printf "\n\n======== Registering default SONATA administrator user to GTKUSR ==\n\n\n"
resp=$(curl -qSfsw '\n%{http_code}' -H "Content-Type: application/json" -H "Authorization: Bearer $token" \
-d "$(admin_reg_data)" \
-X POST $KEYCLOAK_URL/auth/admin/realms/sonata/users) # http://son-gtkusr:5600/api/v1/register/user)
echo $resp
code=$(echo "$resp" | tail -n1)
echo "Code: $code"

# Add role=admin to default admin user
$KCADMIN_SCRIPT add-roles --uusername $SONATA_USER --rolename admin -r $SONATA_REALM

# Get default admin user data
resp=$($KCADMIN_SCRIPT get users -r $SONATA_REALM -q username=$SONATA_USER)
echo "GET_USERS="$resp

# Parse default admin user data to get "id"
USER_ID=$(echo $resp | python -mjson.tool | grep "id" | awk -F ':[ \t]*' '{print $2}' | sed 's/,//g' | sed 's/"//g')
echo "USER_ID="$USER_ID

# Update default admin user credentials
$KCADMIN_SCRIPT update users/$USER_ID/reset-password -r $SONATA_REALM -s type=password -s value=$SONATA_PASSWORD -s temporary=false -n

# Get groups data
resp=$($KCADMIN_SCRIPT get groups -r $SONATA_REALM)
echo "GET_GROUPS="$resp
group_data0=$(echo $resp | awk '{print $0}' | python -mjson.tool | awk '/"id"/' | awk -F ':[ \t]*' '{print $2}' | sed 's/,//g' | sed 's/"//g' )
group_data1=$(echo $resp | awk '{print $0}' | python -mjson.tool | awk '/"name"/' | awk -F ':[ \t]*' '{print $2}' | sed 's/,//g' | sed 's/"//g' )
echo $group_data0
echo $group_data1

# Obtain Admins group identifier
count=1
LINES=`echo $group_data1`
for LINE in $LINES ; do
    if [ "$LINE" == "admins" ]; then
        echo "$count"
        echo $LINE
        GROUP_ID=$(echo $group_data0 |  awk -v var=$count '{ print $var }')
        echo $GROUP_ID
    fi
    (( count++ ))
done

# Add default admin user to Admins group
$KCADMIN_SCRIPT update users/$USER_ID/groups/$GROUP_ID -r $SONATA_REALM -s realm=$SONATA_REALM -s userId=$USER_ID -s groupId=$GROUP_ID -n

printf "\n\n======== Registering default Demo User to GTKUSR ==\n\n\n"
resp=$(curl -qSfsw '\n%{http_code}' -H "Content-Type: application/json" -d "$(demo_reg_data)" \
-X POST http://son-gtkusr:5600/api/v1/register/user)
echo $resp

username=$(echo $resp | grep "username")
code=$(echo "$resp" | tail -n1)
echo "Code: $code"