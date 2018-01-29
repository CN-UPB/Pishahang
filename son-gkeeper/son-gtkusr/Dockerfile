FROM ruby:2.4.3-slim-stretch
RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential && \
	apt-get -y install libcurl3 libcurl3-gnutls libcurl4-openssl-dev && \
	rm -rf /var/lib/apt/lists/*
RUN mkdir -p /app
COPY Gemfile /app/
WORKDIR /app
RUN bundle install
COPY . /app
ENV PORT 5600
EXPOSE 5600
WORKDIR /app
ENV USER_MANAGEMENT_URL http://son-gtkusr:5600
ENV SONATA_USER sonata
ENV SONATA_PASSWORD 1234
ENV SONATA_EMAIL sonata.admin@email.com
ENV KEYCLOAK_USER admin
ENV KEYCLOAK_PASSWORD admin
CMD ["rake", "start"]
