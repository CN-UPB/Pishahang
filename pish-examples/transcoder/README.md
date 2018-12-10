## Information about various Transcoders :

There are various transcoders available for video transcoding used to encode from one conversion to other conversion mp4 to avi .
Transcoding is a two step process where original file is decoded into uncompressed format which can be then encoded into the required format.
Following are the list of transcoders widely used for videos and audio file transcoding.

- HandBrake (Windows, OS X, Linux).
- FFmpeg (Windows, OS X, Linux).
- MEncoder (Windows, OS X, Linux).
- Ingex (Linux).
- MediaCoder (Windows).
- Thoggen (Linux).

### HandBrake :
- It is one of the widely used transcoders.It is easy to use due to its GUI feature.
- It is based of fork of FFmpeg library known as Libnav, due to which it supports majority of ffmpeg libraries. Other third party libraries used in handbrake are libvpx and x265 (description of what this libraries does).
- Handbrake supports limited video formats output viz mp4,mkv and TS.
- Handbrakecli is the command line interface for handbrake.
- It works on cross platforms (Windows, mac and linux).
- Handbrake currently has limited support for hardware acceleration. It only supports Intel QuickSync for now.

### FFmpeg:
- It is the widely used transcoder for videos and audios. It is a command line interface tool and doesn't have any GUI for interaction. Uses library such as libswresample, libavcodec , etc (explain about this libraries here).
- Support majority of Video formats as I/O with some device specific such as Apple ProRes and AVID DNxHD.
- Also supports all major Hardware acc (AMD VCE, Intel QuickSync, Nvidia NVENC). Has flexibility over encoders, decoders, muxers and demuxer. Has more htan 100 codecs. Used by well known companies such as VLC, Youtube, iTunes, Google Chrome etc.
- Allows Transcoding on the fly and supports multiple streaming protocols rtmp, rtsp, http, ftp, hls .
