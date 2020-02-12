# Transcoder Multi Version Service


Transcoding is conversion of audio/video encoding between different formats. It is the process of first decoding the content, altering and finally reencoding it in another format. 

Transcoder multi version service is designed to demonstrate the advantage of utilizing heterogeneous hardware. Three different versions, 1) Virtual Machine, 2) Container and Accelerated versions are implemented.

The implementation is based on a well known audio/video processing framework, FFMPEG. 

FFMPEG pipeline is setup with the following components.

1) **Testsrc** - Generates test pattern video frames to mimic a live streaming source
2) **H264 Encoder** - Encodes the incoming frames in h264 encoding format
3) **HLS Muxer** - "Apple HTTP Live Streaming muxer that segments MPEG-TS according to the HTTP Live Streaming (HLS) specification. It creates a playlist file, and one or more segment files. The output filename specifies the playlist filename." This playlist can be played using VLC or any other player that supports HLS playback. 
                               

Testsrc and HLS Muxer remains the same on all the versions and only the H264 Encoder changes specific to the version. This is discussed in the following sections.

## Virtual Machine Version

The VM based transcoder is built with an ubuntu 16.04 base system. Prebuilt FFMPEG binary was installed directly from the default apt-get repo.

The h264 encoder used here is `x264enc` which is designed to be run on any generic CPU. The parameters passed to the encoder is as follows

+ bitrate: **700 kBit/s**
+ resolution: **w=854:h=480**

```                                                     
                 +------------+                      
                 |            |                      
+-----------+    |  H264      |    +-----------+     
|           |    |  Software  |    |           |     
|  Testsrc  ----->  Encoder   -----| HLS Muxer |     
|           |    |  (x264enc) |    |           |     
+-----------+    |            |    +-----------+     
                 +------------+                      
```                                                     

## Container Version

The container based transcoder is built with an ubuntu 18.04 base system.  FFMPEG 4.0.4 is compiled from sources, the build process is part of the Dockerfile.

The h264 encoder used here is `x264enc` which is designed to be run on any generic CPU. The parameters passed to the encoder is as follows

+ bitrate: **700 kBit/s**
+ resolution: **w=854:h=480**

```                                                     
                 +------------+                      
                 |            |                      
+-----------+    |  H264      |    +-----------+     
|           |    |  Software  |    |           |     
|  Testsrc  ----->  Encoder   -----| HLS Muxer |     
|           |    |  (x264enc) |    |           |     
+-----------+    |            |    +-----------+     
                 +------------+                      
```                                                     


## Accelerated Version
The container based transcoder is built with an ubuntu 18.04 base system with support for Nvidia drivers. FFMPEG 4.0.4 is compiled from sources and along with it libraries to support nvidia hardware based h264 libraries are compiled. The build process is part of the Dockerfile.

The drivers to support Nvidia hardware encoding is part of the docker container. The host system should have CUDA drivers installed so that the accelerated version can utilize it. 

Nvidia provides a base docker container (`nvidia/cudagl:9.2-devel-ubuntu18.04`) that provides an environment for developing applications that utilize nvidia cuda cores.

This docker container is orchestrated using kubernetes just like any other docker container. But this container is equipped with drivers to utilize GPU that is available on the host system.

The h264 encoder used here is `h264_nvenc` which is designed to utilize Nvidia GPU. The parameters passed to the encoder is as follows

+ bitrate: **6000 kBit/s**
+ resolution: **w=1920:h=1080**

```                                                     
                 +------------+                      
                 |            |                      
+-----------+    |  H264      |    +-----------+     
|           |    |  Hardware  |    |           |     
|  Testsrc  ----->  Encoder   -----| HLS Muxer |     
|           |    |  (nvenc)   |    |           |     
+-----------+    |            |    +-----------+     
                 +------------+                      
                                                     
```                                                     
