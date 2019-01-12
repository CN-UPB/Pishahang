# Copyright (c) 2019 Pishahang
# ALL RIGHTS RESERVED.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#    http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM python:3.4-slim
MAINTAINER Pishahang

# define plugin name once
ENV PLUGIN_BASE pish-mano-sdn
# Configuration
ENV broker_host amqp://guest:guest@son-broker:5672/%2F
ENV broker_exchange son-kernel

ENV url_gk_api http://son-gtkapi:5000/api/v2/
ENV url_nsr_repository http://son-catalogue-repos:4011/records/nsr/
ENV url_vnfr_repository http://son-catalogue-repos:4011/records/vnfr/
ENV url_monitoring_server http://son-monitor-manager:8000/api/v1/

ENV db_host son-postgres
ENV db_port 5432
ENV db_user sonatatest
ENV db_password sonata
ENV db_name vimregistry

RUN apt-get update && apt-get install -y gcc
RUN apt-get install -y python-pip
RUN pip install pyzmq

# add generic project files
ADD son-mano-base /son-mano-base
ADD utils/delayedstart.sh /delayedstart.sh

# install son-mano-base to be able to use the plugin base class etc.
WORKDIR /son-mano-base
RUN python setup.py install

# add plugin related files
WORKDIR /
ADD plugins/${PLUGIN_BASE} /plugins/${PLUGIN_BASE}

# install actual plugin
WORKDIR /plugins/${PLUGIN_BASE}
RUN python setup.py develop

CMD ["pish-mano-sdn"]


