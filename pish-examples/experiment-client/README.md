# Experiment Client

+ Streaming command

vlc --loop --qt-notification 0 --no-qt-error-dialogs http://vimdemo2.cs.upb.de/data/stream_0.m3u8

vlc --loop --qt-notification 0 --no-qt-error-dialogs http://vimdemo2.cs.upb.de/data/stream_0.m3u8 --sout file/ts:stream.xyz

sed -i 's/geteuid/getppid/' /usr/bin/vlc
cvlc http://vimdemo1.cs.upb.de/data/stream_0.m3u8 --sout file/ts:stream.xyz


vlc -I dummy --no-sout-audio --loop --qt-notification 0 --no-qt-error-dialogs http://vimdemo2.cs.upb.de/data/stream_0.m3u8


# Direct to file
vlc -vvv http://vimdemo2.cs.upb.de/data/stream_0.m3u8 --sout "#transcode{acodec=none}:file{dst=/tmp/tmpvid/mov.mp4}"

cvlc -vvv http://vimdemo1.cs.upb.de:9000/data/stream_0.m3u8 --vout=dummy --aout=dummy 



sudo apt install -y curl git
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh