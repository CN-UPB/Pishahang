ARG UBUNTU_VERSION=18.04
ARG GST_VERSION=1.14.5

FROM nvidia/cudagl:10.1-devel-ubuntu${UBUNTU_VERSION} as base

ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES compat32,compute,video

RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

ENV NVIDIA_DRIVER_CAPABILITIES ${NVIDIA_DRIVER_CAPABILITIES}

# RUN apt-get update && apt-get install -y --no-install-recommends \
#         mesa-utils && \
#     rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends \
    apt-utils build-essential sudo git curl \
    autoconf autogen automake libtool autopoint

ENV DEBIAN_FRONTEND noninteractive
ENV TZ=Europe/Berlin
RUN apt-get update && apt-get install -y tzdata

    
RUN apt-get -y install libgstreamer1.0-0 libgstreamer1.0-0-dbg libgstreamer1.0-dev liborc-0.4-0 liborc-0.4-0-dbg liborc-0.4-dev liborc-0.4-doc gir1.2-gst-plugins-base-1.0 gir1.2-gstreamer-1.0 gstreamer1.0-alsa gstreamer1.0-doc gstreamer1.0-omx gstreamer1.0-plugins-bad gstreamer1.0-plugins-bad-dbg gstreamer1.0-plugins-bad-doc gstreamer1.0-plugins-base gstreamer1.0-plugins-base-apps gstreamer1.0-plugins-base-dbg gstreamer1.0-plugins-base-doc gstreamer1.0-plugins-good gstreamer1.0-plugins-good-dbg gstreamer1.0-plugins-good-doc gstreamer1.0-plugins-ugly gstreamer1.0-plugins-ugly-dbg gstreamer1.0-plugins-ugly-doc gstreamer1.0-pulseaudio gstreamer1.0-tools gstreamer1.0-x libgstreamer-plugins-bad1.0-0 libgstreamer-plugins-bad1.0-dev libgstreamer-plugins-base1.0-0 libgstreamer-plugins-base1.0-dev libnvidia-encode-418
# wget libgirepository1.0-dev libgstreamer-plugins-base1.0-dev python3-gi  gir1.2-gst-rtsp-server-1.0

RUN apt-get upgrade -y && apt-get autoremove

COPY nvidia-video/include/* /usr/local/cuda/include/

COPY bashrc /etc/bash.bashrc
RUN chmod a+rwx /etc/bash.bashrc

# RUN mkdir -p /usr/local/bin /patched-lib
# COPY patch.sh docker-entrypoint.sh /usr/local/bin/
# RUN chmod +x /usr/local/bin/patch.sh /usr/local/bin/docker-entrypoint.sh

ARG USER_ID=1000
ARG GROUP_ID=1000

RUN groupadd -g ${GROUP_ID} sim && \
    useradd -m -l -u ${USER_ID} -g sim sim && \
    echo "sim:sim" | chpasswd && adduser sim sudo && \
    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers && \
    usermod -a -G audio,video sim

USER sim
WORKDIR /home/sim/

# RUN git clone -b 0.1.16 --single-branch https://gitlab.freedesktop.org/libnice/libnice.git
# RUN git clone -b master --single-branch https://github.com/sctplab/usrsctp.git
# RUN git clone -b ${GST_VERSION} --single-branch https://gitlab.freedesktop.org/gstreamer/gstreamer.git
# RUN git clone -b ${GST_VERSION} --single-branch https://gitlab.freedesktop.org/gstreamer/gst-plugins-base.git
# RUN git clone -b ${GST_VERSION} --single-branch https://gitlab.freedesktop.org/gstreamer/gst-libav.git
# RUN git clone -b ${GST_VERSION} --single-branch https://gitlab.freedesktop.org/gstreamer/gst-plugins-good.git
# RUN git clone -b ${GST_VERSION} --single-branch https://gitlab.freedesktop.org/gstreamer/gst-plugins-ugly.git
RUN git clone -b 1.14.5 --single-branch https://gitlab.freedesktop.org/gstreamer/gst-plugins-bad.git
RUN git clone -b 1.14.5 --single-branch https://gitlab.freedesktop.org/gstreamer/gst-rtsp-server.git

COPY build_gstreamer.sh build_gstreamer.sh
RUN sudo chmod +x build_gstreamer.sh
RUN ./build_gstreamer.sh

COPY entrypoint.sh entrypoint.sh
RUN sudo chmod +x entrypoint.sh

COPY gst-server.py gst-server.py

# RUN cargo install fd-find ripgrep
# RUN sudo apt-get --purge remove "*libnvidia*" -y

ENV LD_LIBRARY_PATH=/usr/local/lib/
ENV GST_PLUGIN_PATH=/usr/local/lib/gstreamer-1.0/

# ENTRYPOINT ["/home/sim/entrypoint.sh"]
CMD ["/usr/bin/python3", "/home/sim/gst-server.py"]
# CMD ["bash"]

