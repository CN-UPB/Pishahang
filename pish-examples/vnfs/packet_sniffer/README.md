# RTMP packet sniffer

As shown in the following figure, the VNF consists of 4 containers including: 

![alt text](https://github.com/CN-UPB/Pishahang/blob/master/pish-examples/vnfs/packet_sniffer/figures/arc.png)

### (1) RTMP packet sniffer: 

Using python socket library, this container captures all incoming traffic into a specific network interface. Then, it inspects the packets headers and extracts MAC and IP address of all TCP packet with source or destination port number 1935. The pair of MAC and IP addresses are then forwarded to MAC/IP recorder though the message broker. 

### (2) MAC/IP recorder and REST APIs: 

This container listens to a specific topic in massage broker to receives the extracted records of MAC-IP-TimeStamp from packet sniffer. It then saves the record into the MongoDB database. It also provides REST APIs which allows retrieving MAC and IP addresses. The Rest APIs are as follows:

#### `/api/records`  shows all the records
#### `/api/records/mac/<string:ip_address>` retrieves MAC address based on given IP address
#### `/api/records/ip/<string:mac_address>` retrieves IP address based on given MAC address

### (3) Database: 

MangoDB is used as a data base

### (4) Massage broker: 

RabbitMQ is used as a message broker and provides a channel for inter-container communications.

## Building

The following commands in `packet_sniffer` directory should be used to build the containers.

#### RTMP Packet Sniffer

`sudo docker build -t pishahang/rtmp-sniffer -f sniffer/Dockerfile .`

#### MAC/IP recorder and REST APIs

`sudo docker build -t pishahang/rtmp-recorder -f recorder/Dockerfile .`

## Usage

The following instructions work on Ubuntu 16.04. It should also work on other Ubuntu versions but it hasn't been tested.

To run the containers, first, you need to install Docker which can be done using the following command.

```
$ sudo apt-get update
$ sudo apt-get install -y docker.io
```

Now that we have Docker running, you should create a docker network to provide the connectivity between containers. This can be done using the following command.

```
$ sudo docker network create pishahang
```

The next step is to run the containers using the commands below.

(1) Message broker
```
sudo docker run -d -p 5672:5672 --name broker --net=pishahang rabbitmq:3-management
```
(2) MongoDB
```
sudo docker run -d -p 27017:27017 --name mongo --net=pishahang mongo
```
(3) RTMP packet sniffer
```
sudo docker run -d --name sniffer --net=pishahang pishahang/rtmp-sniffer
```
(4) MAC/IP recorder and REST APIs
```
sudo docker run -d --name recorder --net=pishahang -p 8001:8001 pishahang/rtmp-recorder
```

Now you can see the status of containers using the following command.

```
sudo docker ps -a
```
## Test

To test the containers, send some traffic to RTMP sniffer to see if it can capture the packets or not. The packet should be sent to the sniffer Ip address. To know the IP address of the container, do the followings:

(1) Access the container terminal: `sudo docker exec -it sniffer /bin/bash`

(2) Then `ifconfig`

To test the APIs you can do the followings:

(1) Getting all records: `curl -X GET -H "Content-Type: application/json" http://localhost:8001/api/records`

(2) Getting specific Mac address: `curl -X GET -H "Content-Type: application/json" http://localhost:8001/api/records/mac/<IP address>`

(3) Getting specific IP address: `curl -X GET -H "Content-Type: application/json" http://localhost:8001/api/records/ip/<MAC address>`

