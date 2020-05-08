FROM        ubuntu:18.04 AS devel-base

WORKDIR     /tmp/workdir

RUN     apt-get update && apt-get install -y software-properties-common && \
        apt-get install -yq --no-install-recommends ca-certificates expat g++  python3-setuptools libgomp1 python3 python3-dev python3-pip libev-dev libevdev2 && \
        apt-get autoremove -y && \
        apt-get clean -y


COPY ./app/cpu.c /cpu.c
RUN  gcc /cpu.c -o /cpu

COPY ./app /app

WORKDIR /app

RUN pip3 install -r requirements.txt

COPY ./app/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

# ENV FLASK_APP=main.py
# ENV FLASK_DEBUG=1

# CMD ["flask", "run", "--host=0.0.0.0", "--port=80"]
# CMD ["bash"]
