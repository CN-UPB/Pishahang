# Install required packages
apt-get install zlib1g-dev uuid-dev libuv1-dev liblz4-dev libjudy-dev libssl-dev libmnl-dev gcc make git autoconf autoconf-archive autogen automake pkg-config curl python

# download it - the directory 'netdata' will be created
git clone --branch v1.19.0 https://github.com/netdata/netdata.git --depth=100
cd netdata

# run script with root privileges to build, install, start Netdata
./netdata-installer.sh
