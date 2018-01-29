### Functional tests
### Variables
if ! [ -z "$ENV_INT_SERVER" ] 
then
    server=$ENV_INT_SERVER
    echo "setting $ENV_INT_SERVER"
else
    server="localhost"
    echo "localhost"
fi

### Check if User Manager is ready
while [ true ]
do
    usermanager=`curl http://$server:5600/admin/log | grep  "User Management is configured and ready"`
    if [ -z "$usermanager" ]
    then
            echo "UM has not started yet"
    else
            echo "UM has started"
            break
    fi
    sleep 10
done

set -x
set -e

# Create a user
NONCE=$(date +%s)
USER="sonata-$NONCE"
PASSWORD="1234"
# returns {"username":"sonata","uuid":"9f107932-19b0-4e9e-87e9-3b0b2ec318a7"}
REGISTER_RESPONSE=$(curl -qSfsw '\n%{http_code}' -d '{"username":"'$USER'","password":"'$PASSWORD'","user_type":"developer","email":"'"$USER"'@sonata-nfv.eu"}' $server:32001/api/v2/users)
echo "REGISTER_RESPONSE was $REGISTER_RESPONSE"
RESP=$(curl -qSfs -d '{"username":"sonata-'$NONCE'","password":"1234"}' http://$server:32001/api/v2/sessions)
echo "User $USER logged in: $RESP"
token=$(echo $RESP | jq -r '.token.access_token')
echo "TOKEN="$token

SECONDS_PAUSED=1
curl -f -v http://$server:32001/api
curl -f -v -H "Authorization:Bearer $token" http://$server:32001/api/v2/packages
echo "Sleeping for $SECONDS_PAUSED..."
sleep $SECONDS_PAUSED
curl -f -v -H "Authorization:Bearer $token" http://$server:32001/api/v2/services
echo "Sleeping for $SECONDS_PAUSED..."
sleep $SECONDS_PAUSED
curl -f -v -H "Authorization:Bearer $token" http://$server:32001/api/v2/functions
echo "Sleeping for $SECONDS_PAUSED..."
sleep $SECONDS_PAUSED
curl -f -v -H "Authorization:Bearer $token" http://$server:32001/api/v2/requests
echo "Sleeping for $SECONDS_PAUSED..."
sleep $SECONDS_PAUSED
curl -f -v -H "Authorization:Bearer $token" http://$server:32001/api/v2/records/services
echo "Sleeping for $SECONDS_PAUSED..."
sleep $SECONDS_PAUSED
curl -f -v -H "Authorization:Bearer $token" http://$server:32001/api/v2/records/functions
echo "Sleeping for $SECONDS_PAUSED..."
sleep $SECONDS_PAUSED
curl -f -v -H "Authorization:Bearer $token" http://$server:32001/api/v2/admin/logs
echo "Sleeping for $SECONDS_PAUSED..."
sleep $SECONDS_PAUSED
curl -f -v -H "Authorization:Bearer $token" http://$server:32001/api/v2/admin/services/logs
echo "Sleeping for $SECONDS_PAUSED..."
sleep $SECONDS_PAUSED
curl -f -v -H "Authorization:Bearer $token" http://$server:32001/api/v2/admin/packages/logs
echo "Sleeping for $SECONDS_PAUSED..."
sleep $SECONDS_PAUSED
curl -f -v -H "Authorization:Bearer $token" http://$server:32001/api/v2/admin/records/logs