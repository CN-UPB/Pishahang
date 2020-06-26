#!/bin/bash
set -e

VERSION=0.12.28

curl "https://releases.hashicorp.com/terraform/${VERSION}/terraform_${VERSION}_linux_amd64.zip" \
    -o terraform.zip -sS
unzip -qo terraform.zip
rm terraform.zip
