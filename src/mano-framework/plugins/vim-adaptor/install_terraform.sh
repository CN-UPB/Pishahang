#!/bin/bash
set -e

curl https://releases.hashicorp.com/terraform/0.12.25/terraform_0.12.25_linux_amd64.zip \
    -o terraform.zip -sS
unzip -qo terraform.zip
rm terraform.zip
