#!/usr/bin/env bash

dir=$(cd -P -- "$(dirname -- "$0")" && pwd -P)

echo "$dir"

sudo docker stop experiment-client
sudo docker rm experiment-client

sudo docker run -id --name experiment-client -v "$(pwd)/app:/app" -p 8888:8888 -e USERID=1000 experiment-client

sudo docker logs experiment-client -f
# sudo docker exec -it experiment-client bash