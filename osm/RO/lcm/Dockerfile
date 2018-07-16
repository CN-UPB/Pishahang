FROM ubuntu:16.04

# Set the working directory to /app
WORKDIR /app/osm_lcm

# Copy the current directory contents into the container at /app
ADD . /app

RUN apt-get update && apt-get install -y git python3 \
    python3-pip python3-pymongo python3-yaml python3-aiohttp \
    python3-stdeb python3-setuptools python3-all python-all \
    python3-bitarray python3-regex python3-lxml debhelper dh-python tox wget \
    python3-cffi \
    && pip3 install pip==9.0.3 \
    && pip3 install -U aiokafka pyang lxml six enum34

RUN git clone https://osm.etsi.org/gerrit/osm/N2VC.git \
    && cd N2VC \
    && cd modules/libjuju && python3 setup.py develop && cd ../.. \
    && pip3 install -U -r requirements.txt \
    && python3 setup.py develop \
    && cd ..

RUN mkdir -p /app/storage/kafka && mkdir -p /app/log


LABEL Maintainer="alfonso.tiernosepulveda@telefonica.com" \
      Description="This implements a north bound interface for OSM" \
      Version="1.0" \
      Author="Alfonso Tierno"

# Used for local storage
VOLUME /app/storage
# Used for logs
VOLUME /app/log

# The following ENV can be added with "docker run -e xxx' to configure
# RO
ENV OSMLCM_RO_HOST         ro
ENV OSMLCM_RO_PORT         9090
ENV OSMLCM_RO_TENANT       osm

# VCA
ENV OSMLCM_VCA_HOST        vca
ENV OSMLCM_VCA_PORT:       17070
ENV OSMLCM_VCA_USER:       admin
ENV OSMLCM_VCA_SECRET:     secret

# database
ENV OSMLCM_DATABASE_DRIVER mongo
ENV OSMLCM_DATABASE_HOST   mongo
ENV OSMLCM_DATABASE_PORT   27017
ENV OSMLCM_STORAGE_DRIVER  local
ENV OSMLCM_STORAGE_PATH    /app/storage

# message
ENV OSMLCM_MESSAGE_DRIVER  kafka
ENV OSMLCM_MESSAGE_HOST    kafka
ENV OSMLCM_MESSAGE_PORT    9092

ENV PYTHONPATH             /app/osm_common
# Run app.py when the container launches
CMD ["python3", "lcm.py"]
