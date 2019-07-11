#!/bin/bash
sudo yum update
wget https://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-8.noarch.rpm
sudo rpm -ihv epel-release-7-8.noarch.rpm
sudo yum update
sudo yum install ansible -y
sudo yum install git -y
sudo yum install htop nmap sysstat tree -y
# DEPLOY SONATA SP
git clone https://github.com/sonata-nfv/son-install.git
cd son-install
ansible-playbook son-cmud.yml -e "target=localhost env=int operation=install service=all"
