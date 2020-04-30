# https://stackoverflow.com/questions/16515099/saving-a-stream-while-playing-it-using-libvlc
# vlc your_input_file_or_stream_here --sout="#std{access=file,mux=ps,dst=go.mpg}" 
import vlc
import os
import time

filepath = 'http://vimdemo1.cs.upb.de:9000/data/stream_1.m3u8'

movie = os.path.expanduser(filepath)
instance = vlc.Instance("--vout=dummy --aout=dummy".split())
media = instance.media_new(movie)
player = instance.media_player_new()
player.set_media(media)
player.play()

stats = vlc.MediaStats() 
# media.get_stats(stats)
# print(stats)

while(1):
    media.get_stats(stats)
    # print(stats)
    print("Bitrate")
    print(stats.demux_bitrate*8000.0)
    time.sleep(1)

player.stop()
