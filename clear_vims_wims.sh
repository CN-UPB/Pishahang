#!/usr/bin/env bash

echo "!!!!! Deleting the following VIMs !!!!!"
sudo docker exec son-postgres psql -h localhost -U postgres -d vimregistry -c "SELECT uuid,endpoint FROM VIM"

sudo docker exec son-postgres psql -h localhost -U postgres -d vimregistry -c "DELETE FROM VIM"

echo ">>>>> Confirming VIMs Deletion !!!!!"
sudo docker exec son-postgres psql -h localhost -U postgres -d vimregistry -c "SELECT uuid,endpoint FROM VIM"

echo "!!!!!!!!!!!!!!!!"

echo "!!!!! Deleting the following WIMs and connections !!!!!"

sudo docker exec son-postgres psql -h localhost -U postgres -d wimregistry -c "SELECT * FROM attached_vim"
sudo docker exec son-postgres psql -h localhost -U postgres -d wimregistry -c "SELECT * FROM wim"

sudo docker exec son-postgres psql -h localhost -U postgres -d wimregistry -c "DELETE FROM attached_vim"
sudo docker exec son-postgres psql -h localhost -U postgres -d wimregistry -c "DELETE FROM wim"

echo ">>>>> Confirming VIMs Deletion !!!!!"
sudo docker exec son-postgres psql -h localhost -U postgres -d wimregistry -c "SELECT * FROM attached_vim"
sudo docker exec son-postgres psql -h localhost -U postgres -d wimregistry -c "SELECT * FROM wim"

echo "!!!!!!!!!!!!!!!!\n\n"
