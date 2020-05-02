echo "Running plugin installer"

pkill python3

python3  /plugins/son-mano-mv/switch_server/app.py > server.logs &

python setup.py develop

son-mano-mv