#!/usr/bin/env bash
cd ~

apt-get install --assume-yes jq

# Get URLs for most recent versions
terraform_url=$(curl https://releases.hashicorp.com/index.json | jq '{terraform}' | egrep "linux.*amd64" | sort --version-sort -r | head -1 | awk -F[\"] '{print $4}')

# Download Terraform. URI: https://www.terraform.io/downloads.html
echo "Downloading $terraform_url."
curl -o terraform.zip $terraform_url

# Unzip and install
unzip terraform.zip
rm terraform.zip

# Enable plugin cache
echo 'plugin_cache_dir   = "/root/.terraform.d/plugin-cache"' >> ~/.terraformrc
