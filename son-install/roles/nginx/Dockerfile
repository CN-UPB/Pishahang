#
# Nginx Dockerfile
#

# Pull base image: latest Ubuntu
FROM ubuntu

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y apt-utils build-essential

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys ABF5BD827BD9BF62
# Add NGINX's repository. 
RUN echo "deb http://nginx.org/packages/ubuntu/ xenial nginx" > /etc/apt/sources.list.d/nginx.list
#RUN echo "deb-src http://nginx.org/packages/ubuntu/ xenial nginx" > /etc/apt/sources.list.d/nginx.list
RUN apt-get install -y software-properties-common && add-apt-repository -y ppa:nginx/stable && apt-get update

# Install Nginx
RUN apt-get update && apt-get install -y nginx && apt-get autoremove

RUN rm -rf /var/lib/apt/lists/* && \
  echo "\ndaemon off;" >> /etc/nginx/nginx.conf && \
  chown -R www-data:www-data /usr/lib/nginx

# Define mountable directories.
VOLUME ["/etc/nginx", "/var/log/nginx", "/usr/share/nginx/html"]

# Define working directory.
WORKDIR /etc/nginx

# Define default command.
CMD ["nginx"]

# Expose ports.
EXPOSE 80
EXPOSE 443
