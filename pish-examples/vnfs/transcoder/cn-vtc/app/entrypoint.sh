#!/usr/bin/env bash
# ln -s  /tmp /var/www/html/data

/etc/init.d/apache2 start

ffmpeg -f lavfi -re -i "aevalsrc=if(eq(floor(t)\,ld(2))\,st(0\,random(4)*3000+1000))\;st(2\,floor(t)+1)\;st(1\,mod(t\,1))\;(0.6*sin(1*ld(0)*ld(1))+0.4*sin(2*ld(0)*ld(1)))*exp(-4*ld(1)) [out1]; testsrc=size=1920x1080:rate=30,drawtext=borderw=15:fontcolor=white:fontfile=/FreeSerif.ttf:fontsize=80:text='ACC - %{localtime}/%{pts\:hms}':x=\(w-text_w\)/2:y=\(h-text_h-line_h\)/3 [out0]" \
    -filter_complex "[v:0]split=2[vout001][vout002];[vout001]scale=w=854:h=480[vout001]" \
    -acodec aac \
    -map [vout001] -c:v:0 h264_nvenc -b:v:0 700k \
    -map [vout002] -c:v:1 h264_nvenc -b:v:1 6000k \
    -map a:0 -map a:0 -c:a aac -b:a 128k -ac 2 \
    -f hls \
    -hls_time 4 \
    -hls_list_size 4 \
    -hls_flags delete_segments \
    -master_pl_name master.m3u8 \
    -var_stream_map "v:0,a:0 v:1,a:1" /tmp/stream_%v.m3u8

