# ffmpeg - http://ffmpeg.org/download.html
#
# From https://trac.ffmpeg.org/wiki/CompilationGuide/Ubuntu
#
# reffered from for nvidia build r/jrottenberg
#
#

FROM        ubuntu:18.04 AS devel-base

WORKDIR     /tmp/workdir



RUN     apt-get update && apt-get install -y software-properties-common && \
        add-apt-repository ppa:jonathonf/ffmpeg-4 -y && \
        apt-get -yqq update && \
        apt-get install -yq --no-install-recommends ca-certificates expat libgomp1 ffmpeg apache2 && \
        apt-get autoremove -y && \
        apt-get clean -y

COPY ./apache2.conf /etc/apache2/apache2.conf
COPY ./mime.conf /etc/apache2/mods-available/mime.conf

RUN ln -s  /tmp /var/www/html/data

COPY ./app/entrypoint.sh /entrypoint.sh
COPY ./app/FreeSerif.ttf /FreeSerif.ttf

RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

# CMD ["flask", "run", "--host=0.0.0.0", "--port=80"]
# CMD ["bash"]
