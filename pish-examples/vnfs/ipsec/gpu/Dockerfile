# ffmpeg - http://ffmpeg.org/download.html
#
# From https://trac.ffmpeg.org/wiki/CompilationGuide/Ubuntu
#
# reffered from for nvidia build r/jrottenberg
#
#

FROM    nvidia/cudagl:9.2-devel-ubuntu18.04 AS devel-base

ENV	    NVIDIA_DRIVER_CAPABILITIES compat32,compute,video
WORKDIR     /tmp/workdir

RUN     apt-get -yqq update && \
        apt-get install -yq --no-install-recommends ca-certificates expat libgomp1 && \
        apt-get autoremove -y && \
        apt-get clean -y

FROM        nvidia/cudagl:9.2-runtime-ubuntu18.04 AS runtime-base

ENV	    NVIDIA_DRIVER_CAPABILITIES compat32,compute,video
WORKDIR     /tmp/workdir

RUN     apt-get -yqq update && \
        apt-get install -yq --no-install-recommends ca-certificates expat libgomp1 libxcb-shape0-dev && \
        apt-get autoremove -y && \
        apt-get clean -y


FROM  devel-base as build

ENV        NVIDIA_HEADERS_VERSION=8.1.24.9
ARG        MAKEFLAGS="-j12"

RUN      buildDeps="autoconf \
                    automake \
                    cmake \
                    curl \
                    bzip2 \
                    libexpat1-dev \
                    g++ \
                    gcc \
                    git \
                    gperf \
                    libtool \
                    make \
                    nasm \
                    perl \
                    pkg-config \
                    python \
                    libssl-dev \
                    yasm \
                    zlib1g-dev" && \
        apt-get -yqq update && \
        apt-get install -yq --no-install-recommends ${buildDeps}

COPY ./app/gpu_ver2.cu /gpu_ver2.cu
RUN  nvcc /gpu_ver2.cu -o /gpu

FROM        runtime-base AS release
# Author Amay Churi

COPY --from=build /usr/local/bin /usr/local/bin/
COPY --from=build /usr/local/share /usr/local/share/
COPY --from=build /usr/local/lib /usr/local/lib/
# COPY --from=build /usr/bin /usr/bin/
COPY --from=build /gpu /gpu

# Apache
COPY ./app /app

RUN apt-get update
RUN apt-get install -y python3 python3-pip libev-dev libevdev2

# COPY ./app/requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3 install -r requirements.txt

# ENV FLASK_APP=main.py
# ENV FLASK_DEBUG=1

COPY ./app/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

# CMD ["flask", "run", "--host=0.0.0.0", "--port=80"]
# CMD ["bash"]
