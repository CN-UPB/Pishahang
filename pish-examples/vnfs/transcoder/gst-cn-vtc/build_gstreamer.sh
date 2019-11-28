#!/usr/bin/env bash

# pushd gstreamer
# ./autogen.sh
# ./configure --disable-gtk-doc
# make -j$(nproc)
# sudo make install
# sudo ldconfig
# popd

# pushd gst-plugins-base
# ./autogen.sh --enable-iso-codes --enable-orc --disable-gtk-doc
# make -j$(nproc)
# sudo make install
# sudo ldconfig
# popd

# pushd gst-plugins-good
# ./autogen.sh --enable-orc --disable-gtk-doc
# make -j$(nproc)
# sudo make install
# sudo ldconfig
# popd

# pushd gst-plugins-ugly
# ./autogen.sh --enable-orc --disable-gtk-doc
# make -j$(nproc)
# sudo make install
# sudo ldconfig
# popd

# pushd gst-libav
# ./autogen.sh --enable-orc --disable-gtk-doc
# make -j$(nproc)
# sudo make install
# sudo ldconfig
# popd

# pushd libnice
#  ./autogen.sh --with-gstreamer --enable-static --enable-static-plugins \
#     --enable-shared --without-gstreamer-0.10 --disable-gtk-doc --enable-compile-warnings=no
# make -j$(nproc)
# sudo make install
# sudo ldconfig
# popd

# pushd usrsctp
# ./bootstrap
# ./configure
# make -j$(nproc)
# sudo make install
# sudo ldconfig
# popd

pushd gst-plugins-bad
NVENCODE_CFLAGS="-I/usr/local/cuda/include/"  NVENCODE_LIBS="-L/usr/local/cuda/lib64/"   \
  ./autogen.sh --enable-orc --disable-gtk-doc --with-cuda-prefix=/usr/local/cuda --disable-openexr --disable-opencv
make -j$(nproc)
sudo make install
sudo ldconfig
popd

pushd gst-rtsp-server
./autogen.sh --disable-gtk-doc
# ./configure --disable-gtk-doc --enable-introspection=yes
make -j$(nproc)
sudo make install
# popd

export LD_LIBRARY_PATH=/usr/local/lib/
export GST_PLUGIN_PATH=/usr/local/lib/gstreamer-1.0/
export NVENCODE_CFLAGS="-I/usr/local/cuda/include/"
export NVENCODE_LIBS="-L/usr/local/cuda/lib64/"

sudo apt-get --purge remove "*libnvidia*" -y

sudo apt install python3-gi  gir1.2-gst-rtsp-server-1.0 -y


# ./examples/test-launch --gst-debug=3 '(videotestsrc ! clockoverlay halignment=right valignment=bottom time-format="%d/%m/%Y %H:%M:%S" ! video/x-raw,width=1280,height=720 ! nvh264enc ! h264parse ! rtph264pay name=pay0 pt=96 )'

# export LC_ALL="en_US.UTF-8"
# export LC_CTYPE="en_US.UTF-8"
# sudo dpkg-reconfigure locales