# Pishahang Installation

Pishahang consists of a set of Docker containers (micro services) that cooperate with each other.
Hence, installing Pishahang means setting up its Docker containers.
There are two ways to do this:

* Using Ansible (stable, but less comfortable to work with in development setups)
* Using Docker Compose (currently being evaluated, more comfortable and less platform-dependent)

The following section describes the installation with Ansible. Head on to [Installation with Docker Compose](#installation-with-docker-compose) if you plan to modify Pishahang.

## Installation with Ansible

This installation has only been tested on Ubuntu 16.04, however, if Ansible, Docker and Git are available, other distributions should work as well. This guide uses a clean Ubuntu 16.04 installation.

### Minimum Requirements

* Memory: 4GB
* Disk: 25GB free space
* A non-root user

### Procedure


#### Install packages

```bash
$ sudo apt install -y software-properties-common
$ sudo apt-add-repository -y ppa:ansible/ansible
$ sudo apt update
$ sudo apt install -y git ansible
```

The rest of the commands should be run by the non-root user account.

#### Clone repository

```bash
$ git clone https://github.com/CN-UPB/Pishahang.git
$ cd Pishahang/pish-install
$ mkdir ~/.ssh
$ echo sonata | tee ~/.ssh/.vault_pass
```

#### Start installation

Replace "\<your\_ip4\_address\>" with the IP address that SONATA GUI and BSS should be available at (the IP address that is publicly accessible).

```bash
$ ansible-playbook utils/deploy/sp.yml -e \
	 "target=localhost public_ip=<your_ip4_address>" -v
```

After the setup has completed, make sure to [verify your installation](#verify-installation).

## Installation with Docker Compose

### Minimum Requirements

* Memory: 4GB
* Disk: 25GB free space

### Procedure

#### Install Docker and Docker Compose

On a clean Ubuntu (>=16.04) VM for development, just run

```bash
$ sudo apt install -y curl git
$ curl -fsSL https://get.docker.com -o get-docker.sh
$ sudo sh get-docker.sh
$ sudo curl -L "https://github.com/docker/compose/releases/download/1.25.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
$ sudo chmod +x /usr/local/bin/docker-compose
$ sudo curl -L https://raw.githubusercontent.com/docker/compose/1.25.3/contrib/completion/bash/docker-compose -o /etc/bash_completion.d/docker-compose
```

On any other machine or in production, follow the official installation instructions for [Docker](https://docs.docker.com/install/) and [Docker Compose](https://docs.docker.com/compose/install/).

#### Clone repository and set up environment

```bash
$ git clone https://github.com/CN-UPB/Pishahang.git && cd Pishahang
```

After that, find out your installation machine's public IP (the one that SONATA GUI and BSS should be available at), and run

```bash
$ ./generate-env.sh <PUBLIC_IP>
```

This creates a local .env file that will be used by Docker Compose.

#### Start Pishahang

Finally, you can set up and start Pishahang:
```bash
$ sudo docker-compose pull
$ sudo docker-compose up -d
```

## Verify installation

Open your browser and navigate to http://public_ip. Log in using the username `pishahang` and password `1234`. If the installation was successful, you should now see the dashboard of the service platform.