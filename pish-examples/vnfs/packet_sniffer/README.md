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
