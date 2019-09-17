#!/usr/bin/env bash

uuid='afe14c70-11ee-4edd-adbb-c0117adc8807'
name='sonata23'
type='compute'
vendor='Heat'
endpoint='131.234.29.169'
username='demo'
domain='default'
configuration='{"tenant_ext_net":"b847dcbc-f587-4c0a-a270-5582824bb4d8","tenant_ext_router":"746df580-730d-4ee6-b4bf-e90a4e4a21e0","tenant":"11174f9f178f449eabd16f95b42b858e"}'
city='Paderborn'
country='Germany'
pass='1234'

wim_uuid='942eebb7-2b97-4130-9f98-260ae9236bc1'
wim_type='WIM'
wim_name='dummy'
wim_vendor="MOCK"
wim_endpoint="default"
wim_username="sonata"
wim_pass="1234"

echo "!!!!! Adding WIM !!!!!"
sudo docker exec son-postgres psql -h localhost -U postgres -d wimregistry -c "INSERT INTO wim VALUES ( '$wim_uuid', '$wim_type', '$wim_name', '$wim_vendor', '$wim_endpoint', '$wim_username', '$wim_pass');"

echo "!!!!! Adding VIM !!!!!"
sudo docker exec son-postgres psql -h localhost -U postgres -d vimregistry -c "INSERT INTO VIM VALUES ( '$uuid', '$name', '$type', '$vendor', '$endpoint', '$username', '$domain', '$configuration', '$city', '$country', '$pass');"

echo "!!!!! Attaching VIM !!!!!"
sudo docker exec son-postgres psql -h localhost -U postgres -d wimregistry -c "INSERT INTO attached_vim VALUES ( '$uuid', '$endpoint', '$wim_uuid');"

echo "############################"
echo "Printing Tables"
echo "############################"
sudo docker exec son-postgres psql -h localhost -U postgres -d wimregistry -c "SELECT * FROM wim"
sudo docker exec son-postgres psql -h localhost -U postgres -d vimregistry -c "SELECT uuid,endpoint FROM VIM"
sudo docker exec son-postgres psql -h localhost -U postgres -d wimregistry -c "SELECT * FROM attached_vim"
