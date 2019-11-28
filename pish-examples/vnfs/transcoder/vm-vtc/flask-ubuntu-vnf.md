# Creating ffmpeg transcoder with flask


sudo add-apt-repository ppa:jonathonf/ffmpeg-4

sudo apt-get update
sudo apt-get install ffmpeg

sudo apt-get install -y python-pip python-dev build-essential

export LC_ALL="en_US.UTF-8"
export LC_CTYPE="en_US.UTF-8"
sudo dpkg-reconfigure locales

# To configure systemd service

sudo systemctl daemon-reload
sudo systemctl enable flask
sudo systemctl restart flask
sudo systemctl status flask


        [Unit]
        Description=Microblog web application
        After=network.target

        [Service]
        User=scramble
        WorkingDirectory=/home/scramble/app
        Environment=FLASK_APP=/home/scramble/app/main.py
        Environment=FLASK_DEBUG=1

        ExecStart=/usr/local/bin/flask run --host=0.0.0.0 --port=8080
        Restart=always

        [Install]
        WantedBy=multi-user.target
