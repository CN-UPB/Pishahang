#! /bin/bash

if [ -z "$1" ]; then
    echo "Usage: generate-env.sh <PUBLIC_IP> [<PUBLIC_DOMAIN_NAME>]"
    exit 1
fi

PUBLIC_DOMAIN_NAME=${2:-$1}

sed -e "s/%{PUBLIC_IP}%/$1/g" -e "s/%{PUBLIC_DOMAIN_NAME}%/$PUBLIC_DOMAIN_NAME/" ./.env.template > .env
