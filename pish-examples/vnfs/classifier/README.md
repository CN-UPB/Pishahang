# Install flask

    export LC_ALL="en_US.UTF-8"
    export LC_CTYPE="en_US.UTF-8"
    sudo dpkg-reconfigure locales

    sudo apt install python-pip
    sudo pip install Flask

# systemd commands

    sudo nano /etc/systemd/system/classifier.service
    sudo systemctl daemon-reload
    sudo systemctl enable classifier.service 
    sudo systemctl restart classifier.service 
    sudo systemctl status classifier.service 

# Add files

    chmod +x switch_vnf.sh 

# Enable forwarding

    sudo sysctl net.ipv4.ip_forward
    sudo sed -i 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/g' /etc/sysctl.conf
    sudo sysctl -p
    sudo sysctl net.ipv4.ip_forward

# API

    curl 127.0.0.1:8080/switch?ip=131.234.250.178\&port=30503
    