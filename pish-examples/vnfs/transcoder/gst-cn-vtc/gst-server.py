def run_async(func):
    from threading import Thread
    from functools import wraps
    @wraps(func)
    def async_func(*args, **kwargs):
        func_hl = Thread(target=func, args=args, kwargs=kwargs)
        func_hl.start()
        return func_hl
    return async_func

import os
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, GstRtspServer

class VOD_Server(object):
    """docstring for VOD_Server."""
    def __init__(self):
        super(VOD_Server, self).__init__()
        GObject.threads_init()
        self.loop = GObject.MainLoop()
        Gst.init(None)

        self.server = GstRtspServer.RTSPServer()
        self.server.set_service('9000')
        self.server.attach(None)
        self.run()

    def SetLaunch(self, uri):

        factory = GstRtspServer.RTSPMediaFactory()

        # factory.set_launch("( uridecodebin uri={location} name=d d. ! queue ! videoconvert ! videoscale ! video/x-raw,width=480, height=240   ! queue ! nvh264enc preset=low-latency-hp bitrate=20000 ! queue !  h264parse ! video/x-h264,stream-format=byte-stream ! rtph264pay name=pay0 pt=96 config-interval=1 d. ! queue ! audioconvert ! avenc_aac ! rtpmp4apay pt=97 name=pay1 config-interval=1 )".format(location=uri))

        factory.set_launch('( videotestsrc  is-live=1 ! clockoverlay halignment=center valignment=center time-format="%d/%m/%Y %H:%M:%S" font-desc="60px" ! video/x-raw,width=854,height=480 ! queue ! nvh264enc preset=5 bitrate=800 rc-mode=3 ! queue ! h264parse ! queue ! rtph264pay name=pay0 pt=96 )')

        # factory.set_shared(True)
        # factory.set_suspend_mode(1)
        factory.set_eos_shutdown(True)
        self.server.get_mount_points().add_factory("/{}".format("480"), factory)

        print(self.server.get_mount_points())

        # Second

        factory2 = GstRtspServer.RTSPMediaFactory()

        # factory2.set_launch("( uridecodebin uri={location} name=d d. ! queue ! videoconvert ! videoscale ! video/x-raw,width=1920, height=1080  ! queue ! nvh264enc ! queue !  h264parse ! video/x-h264,stream-format=byte-stream ! rtph264pay name=pay0 pt=96 d. ! queue ! audioconvert ! avenc_aac ! rtpmp4apay pt=97 name=pay1 )".format(location=uri))

        factory2.set_launch('( videotestsrc  is-live=1 ! clockoverlay halignment=center valignment=center time-format="%d/%m/%Y %H:%M:%S" font-desc="60px" ! video/x-raw,width=1920,height=1080 ! queue ! nvh264enc preset=5 bitrate=8000 rc-mode=3 ! queue ! h264parse ! queue ! rtph264pay name=pay0 pt=96 )')

        # factory2.set_shared(True)
        factory2.set_eos_shutdown(True)
        self.server.get_mount_points().add_factory("/{}".format("1080"), factory2)

        factory3 = GstRtspServer.RTSPMediaFactory()

        # factory2.set_launch("( uridecodebin uri={location} name=d d. ! queue ! videoconvert ! videoscale ! video/x-raw,width=1920, height=1080  ! queue ! nvh264enc ! queue !  h264parse ! video/x-h264,stream-format=byte-stream ! rtph264pay name=pay0 pt=96 d. ! queue ! audioconvert ! avenc_aac ! rtpmp4apay pt=97 name=pay1 )".format(location=uri))

        factory3.set_launch('( videotestsrc  is-live=1 ! clockoverlay halignment=center valignment=center time-format="%d/%m/%Y %H:%M:%S" font-desc="60px" ! video/x-raw,width=3840,height=2160 ! queue ! nvh264enc preset=5 bitrate=12000 rc-mode=3 ! queue ! h264parse ! queue ! rtph264pay name=pay0 pt=96 )')

        # factory2.set_shared(True)
        factory3.set_eos_shutdown(True)
        self.server.get_mount_points().add_factory("/{}".format("4k"), factory3)
        print(self.server.get_mount_points())

    def DelLaunch(self):
        self.server.get_mount_points().remove_factory("/{}".format(self.oldpath))

    @run_async
    def run(self):
        self.loop.run()

mp4_ext_uri = "http://distribution.bbb3d.renderfarming.net/video/mp4/bbb_sunflower_1080p_30fps_normal.mp4"

v = VOD_Server()
v.SetLaunch(mp4_ext_uri)
# v.SetLaunch("1484296083", "event")
# v.SetLaunch("1483609565", "event")
