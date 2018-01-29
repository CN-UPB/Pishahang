#!/bin/bash

/setenv.sh

echo "Waiting for rabbitmq on port" $broker_port

while ! nc -z $broker_host $broker_port; do
  sleep 1 && echo -n .; # waiting for rabbitmq
done;

echo "Waiting for postgresql on port" $repo_port

while ! nc -z $repo_host $repo_port; do
  sleep 1 && echo -n .; # waiting for postgresql
done;

service wim-adaptor start
