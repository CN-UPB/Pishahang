#!/bin/bash
wget https://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-8.noarch.rpm
sudo rpm -ihv epel-release-7-8.noarch.rpm
sudo yum update
sudo yum install ansible -y
sudo yum install git python-netaddr -y
sudo yum install htop nmap sysstat tree -y

