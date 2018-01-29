FROM ruby:2.4.3-slim-stretch
RUN apt-get update && \
  apt-get install -y --no-install-recommends build-essential libcurl3 libcurl3-gnutls libcurl4-openssl-dev && \
  rm -rf /var/lib/apt/lists/*
RUN mkdir -p /app/log
WORKDIR /app
COPY Gemfile /app
RUN bundle install
COPY . /app
EXPOSE 5150
WORKDIR /app
ENV PORT 5150
ENV REDIS_URL redis://127.0.0.1:6379
CMD ["bundle", "exec", "puma", "-C", "config/puma.rb", "-b", "tcp://0.0.0.0:5150"]

