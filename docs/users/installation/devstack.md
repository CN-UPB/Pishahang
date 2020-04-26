# DevStack Installation

### Requirements

* Ubuntu 16.04
* At least a network interface with an IP address already assigned
* At least 2 cores (or more, depending on number of VMs)
* 8 GB RAM (or more, depending on number of VMs)
* 40 GB Disk

### Step 1: Prerequisites

Install prerequisites and create user ``stack``

```console
$ sudo apt-get update
$ sudo apt-get install -y git

$ sudo useradd -s /bin/bash -d /opt/stack -m stack
$ echo "stack ALL=(ALL) NOPASSWD: ALL" \
    | sudo tee /etc/sudoers.d/stack
```

Switch to user ``stack`` and checkout ``ocata`` branch

```console
$ sudo su - stack
$ git clone https://git.openstack.org/openstack-dev/devstack
$ cd devstack
$ git checkout stable/ocata
```
### Step 2: Install DevStack

Create a local.conf file in the devstack directory and populate it with the content of [this](https://github.com/CN-UPB/Pishahang/blob/master/osm/documentation/devstack/local.conf) file. Inside the file, lines 28-31, Ip addreses must be adapted to match the IP address of the network interface that should be used. Lines 44-48, you can set your desired password for different components of devstack. Lines 121-125 are related to devstack networking configuration.  We use the ``PROVIDER``-network option where guests are spawned in the same network as the Devstack-controller. Change the value of these elements wherever needed and save the file. Then run the following command.

```console
$ ./stack.sh
## This can take 20+ minutes.
```
With the successful installation of devstack, you should access devstack dashboard via this link: ``http://<HOST_IP>/dashboard``

### Step 3: Create new user and project
Login as admin user in domain Default and create a new user (e.g. pishahang) under the OpenStack dashboard menu Identity->User (Create User). **While creating the user also add a new project (e.g. pish-project, remember project and tenant is the same) and allocate the maximum number of resources for that project under Quotas tab (OpenStack Project Quotas). This is important otherwise the deployment of service from Sonata will fail. Also, give the admin role to the new user so that it has all the access otherwise the deployment may fail.**

### Step 4: Configure guest VM connectivity

At this point DevStack is running but connectivity of guest VMs is limited (No internet access, hence no downloading of software to run on guest VMs; one cannot ssh into guest VMs).
To enable internet access from guest VMs an iptables rule needs to be added.

Modify ``eth0`` to match the interface name with the IP address configured above (``HOST_IP``).

```console
$ sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
```

To be able to ssh into guest VMs security group rules of OpenStack need to be modified.

```console
$ source devstack/accrc/admin/admin

$ openstack security group rule create --proto icmp --dst-port 0 default
$ openstack security group rule create --proto tcp --dst-port 22 default
$ nova secgroup-add-rule default icmp -1 -1 0.0.0.0/0
$ nova secgroup-add-rule default tcp 22 22 0.0.0.0/0
```


### Usage hints

#### User credentials

As user ``stack`` one has to ``source`` the admin credentials located in ``/opt/stack/devstack/accrc/admin/admin`` before being able to issue commands starting with ``openstack``, like ``openstack network list`` (There is also a ``demo`` account that is created automatically in ``/opt/stack/devstack/accrc/demo/demo`` which has less privileges).

Example:

```console
$ source /opt/stack/devstack/accrc/admin/admin
$ openstack project list
$ openstack network list
```

#### Reboot

After a reboot of the machine DevStack will not run anymore.
Login as user ``stack`` and re-run

```console
$ /opt/stack/devstack/stack.sh
```