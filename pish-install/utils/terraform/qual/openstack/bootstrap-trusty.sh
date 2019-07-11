#!/bin/bash
sudo apt-get install software-properties-common -y
sudo apt-add-repository ppa:ansible/ansible
sudo apt-get update
sudo apt-get install ansible -y
sudo apt-get install git -y
sudo apt-get install htop nmap sysstat tree -y
# DEPLOY SONATA SP
git clone https://github.com/sonata-nfv/son-install.git
cd son-install
ansible-playbook son-cmud.yml -e "target=localhost operation=install service=all"

