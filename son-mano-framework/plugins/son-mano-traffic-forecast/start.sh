echo "Running plugin installer"

rm /plugins/son-mano-traffic-forecast/models/*

python setup.py develop

son-mano-traffic-forecast