## VM based transcoder documentation

- After launching an instance on Devstack ssh into the instance using a key-value pair or pem certificate.

`ffmpeg` - transcoder being used for conversion.

`-i file.mp4` - If the file is present locally within the system.

`-i external link` - If the source is an external link.

`-vf scale=1920x1080,setdar=16:10` Provide videos resolutions and display ratio for the screen. 

We can set scale with following values - `1920x1080', '1920x720', '480x720`, '480x240'. 

Display ratio can be set to following values - `4:3`, `8:10`, `16:10`, `16:9`

`-movflags` is used for pass filter in the transcoder. 

`-f mp4 destination source/file` We can provide `mpegts` for streaming content

`-b:v 30M -maxrate 30M -bufsize 30M ` Setting bitrates and buffer sizes for transcoding.

### External source is been transcoded
```
ffmpeg -i udp://131.234.250.178:2205 \
       -b:v 30M -maxrate 30M -bufsize 30M \
       -vf scale=1920x1080,setdar=16:10 \
       -movflags frag_keyframe+empty_moov \
       -f mp4 udp://131.234.250.178:2200

```
Open `ffplay -i udp://131.234.250.178:2205` in terminal to view live stream.


### Transcoding local file
```
ffmpeg -i file.mp4 \
       -b:v 30M -maxrate 30M -bufsize 30M \
       -vf scale=1920x1080,setdar=16:10 \
       -movflags frag_keyframe+empty_moov \
       -f mp4 udp://131.234.250.178:2200

```

Open `ffplay -i udp://131.234.250.178:2205` in terminal to view live stream.

