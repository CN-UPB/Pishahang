# Pishahang Installation

Pishahang consists of a set of Docker containers (micro services) that cooperate with each other.
Hence, installing Pishahang means setting up its Docker containers.

## Minimum Requirements

* Memory: 4GB
* Disk: 25GB free space

## Procedure

### Install Docker and Docker Compose

On a clean Ubuntu (>=16.04) VM for development, just run

```bash
sudo apt install -y curl git
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/download/1.25.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo curl -L https://raw.githubusercontent.com/docker/compose/1.25.3/contrib/completion/bash/docker-compose -o /etc/bash_completion.d/docker-compose
```

On any other machine or in production, follow the official installation instructions for [Docker](https://docs.docker.com/install/) and [Docker Compose](https://docs.docker.com/compose/install/).

### Clone repository and set up environment

```bash
git clone https://github.com/CN-UPB/Pishahang.git && cd Pishahang
```

After that, copy the `.env.template` file to `.env` (e.g., `cp .env.template .env`)
The `.env` file will be used by Docker Compose and contains initial user data and passwords, as well as the Pishahang version.

### Start Pishahang

Finally, you can set up and start Pishahang:

```bash
sudo docker-compose pull
sudo docker-compose up -d
```

## Verify installation

Open your browser and navigate to `http://<public_ip>`.
Log in using the username `pishahang` and password `1234`.
