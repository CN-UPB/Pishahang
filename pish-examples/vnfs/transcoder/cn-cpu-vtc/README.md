## Container CNF documentation
Download container - `docker pull fellonoverhere45/pishahang-cnf:nvidia-ffmpeg-4`

[Docker hub link](https://hub.docker.com/r/fellonoverhere45/pishahang-cnf/tags)

`fellonoverhere45/pishahang-cnf:nvidia-ffmpeg-4` Docker container.

`--add-host="localhost:ipaddr"` - Add host IP address to where you want to stream.

` -vf scale_npp=-1:480` Provide Scale such as `1:1080`, `1:720`, `1:480`, `1:240`

`-v $HOME/Downloads:/tmp/workdir` If you want to transcode local file mount the volume to `\tmp\workdir` inside the container.

`--runtime=nvidia` Provide ENV for the container.

`-hwaccel_device 0  -hwaccel cuvid  -c:v h264_cuvid` Enabling hardware acceleration.

`-i file.mp4` If the volume is mounted.

`-i https://www.radiantmediaplayer.com/media/bbb-360p.mp4` If the source is an external link.

### Example of `volume mounted` with saving output file in the local directory.

```
docker run --rm -it --runtime=nvidia \
           -v $HOME/Downloads:/tmp/workdir \
           fellonoverhere45/pishahang-cnf:nvidia-ffmpeg-4 \
           -hwaccel_device 0  -hwaccel cuvid  \ 
           -c:v h264_cuvid -i big_bunny_1080p_30.mp4 \
           -c:v hevc_nvenc -vf scale_npp=-1:480 \
            -f mp4 output.mp4
```

### Example of `volume mounted` with streaming to IP address.

Since we are streaming mp4 output is not supported for seeking. We use mpegts stream.

```
 docker run --add-host="localhost:131.234.250.178" \
           --rm -it --runtime=nvidia \
           -v $HOME/Downloads:/tmp/workdir \
           fellonoverhere45/pishahang-cnf:nvidia-ffmpeg-4  \
           -hwaccel_device 0       -hwaccel cuvid  \
           -c:v h264_cuvid       -i big_bunny_1080p_30.mp4  \
           -c:v hevc_nvenc -vf scale_npp=-1:480  \
           -f mpegts udp://131.234.250.178:2205 
  ```

Open `ffplay -i udp://131.234.250.178:2205` in terminal to view live stream.


### Example of `External link` with streaming to IP address.

```
 docker run --add-host="localhost:131.234.250.178" \
           --rm -it --runtime=nvidia \
           -v $HOME/Downloads:/tmp/workdir \
           fellonoverhere45/pishahang-cnf:nvidia-ffmpeg-4  \
           -hwaccel_device 0       -hwaccel cuvid  \
           -c:v h264_cuvid       -i https://www.radiantmediaplayer.com/media/bbb-360p.mp4 \
           -c:v hevc_nvenc -vf scale_npp=-1:480  \
           -f mpegts udp://131.234.250.178:2205 
  ```

Open `ffplay -i udp://131.234.250.178:2205` in terminal to view live stream.


### Enable bash for scripting within the container
 ```
docker run -it --entrypoint='bash' fellonoverhere45/pishahang-cnf:nvidia-ffmpeg-4 
```

### dockerhub

docker tag transcoder-cpu-cn:latest pgscramble/transcoder-cpu-cn:1.1
docker push pgscramble/transcoder-cpu-cn:1.0
