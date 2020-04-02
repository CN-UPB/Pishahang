echo "Running plugin installer"

pkill python3

python3  /plugins/son-mano-mv-policy/policy_server/server.py > server.logs &

python setup.py develop

son-mano-mv-policy