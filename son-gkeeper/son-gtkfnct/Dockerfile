FROM ruby:2.4.3-slim-stretch
RUN apt-get update && \
  apt-get install -y --no-install-recommends build-essential libcurl3 libcurl3-gnutls libcurl4-openssl-dev && \
	rm -rf /var/lib/apt/lists/*
RUN mkdir -p /app
WORKDIR /app
COPY Gemfile /app
RUN bundle install
COPY . /app
EXPOSE 5500
WORKDIR /app
ENV CATALOGUES_URL http://catalogues:4002/catalogues/api/v2
ENV PORT 5500
CMD ["bundle", "exec", "puma", "-C", "config/puma.rb", "-b", "tcp://0.0.0.0:5500"]
