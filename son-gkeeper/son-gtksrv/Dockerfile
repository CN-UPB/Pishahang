FROM ruby:2.4.3-slim-stretch
RUN apt-get update && \
  apt-get install -y --no-install-recommends build-essential libcurl3 libcurl3-gnutls libcurl4-openssl-dev libpq-dev && \
	rm -rf /var/lib/apt/lists/*
RUN mkdir -p /app
WORKDIR /app
COPY Gemfile /app
RUN bundle install
COPY . /app
EXPOSE 5300
WORKDIR /app
ENV POSTGRES_PASSWORD sonata
ENV POSTGRES_USER sonatatest
ENV DATABASE_HOST son-postgres
ENV POSTGRES_DB=gatekeeper
ENV DATABASE_PORT 5432
ENV MQSERVER amqp://guest:guest@son-broker:5672
ENV CATALOGUES_URL http://son-catalogue-repos:4011/catalogues/api/v2
ENV PORT 5300
CMD ["bundle", "exec", "puma", "-C", "config/puma.rb", "-b", "tcp://0.0.0.0:5300"]
