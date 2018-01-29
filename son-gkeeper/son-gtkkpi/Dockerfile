FROM ruby:2.4.3-slim-stretch
RUN apt-get update && apt-get install -y --no-install-recommends \
                build-essential \
		libcurl3 \
                libcurl3-gnutls \
                libcurl4-openssl-dev \
                libpq-dev \
                git \
                jq \
                g++ \
                gcc \
                libc6-dev \
                make \
                pkg-config \
                wget \
                && rm -rf /var/lib/apt/lists/*

ENV GOLANG_VERSION 1.7.6
RUN set -eux; \
	\
	dpkgArch="$(dpkg --print-architecture)"; \
	case "${dpkgArch##*-}" in \
		amd64) goRelArch='linux-amd64'; goRelSha256='ad5808bf42b014c22dd7646458f631385003049ded0bb6af2efc7f1f79fa29ea' ;; \
		armhf) goRelArch='linux-armv6l'; goRelSha256='fc5c40fb1f76d0978504b94cd06b5ea6e0e216ba1d494060d081e022540900f8' ;; \
		i386) goRelArch='linux-386'; goRelSha256='99f79d4e0f966f492794963ecbf4b08c16a9a268f2c09053a5ce10b343ee4082' ;; \
		ppc64el) goRelArch='linux-ppc64le'; goRelSha256='8b5b602958396f165a3547a1308ab91ae3f2ad8ecb56063571a37aadc2df2332' ;; \
		s390x) goRelArch='linux-s390x'; goRelSha256='d692643d1ac4f4dea8fb6d949ffa750e974e63ff0ee6ca2a7c38fc7c90da8b5b' ;; \
		*) goRelArch='src'; goRelSha256='1a67a4e688673fdff7ba41e73482b0e59ac5bd0f7acf703bc6d50cc775c5baba'; \
			echo >&2; echo >&2 "warning: current architecture ($dpkgArch) does not have a corresponding Go binary release; will be building from source"; echo >&2 ;; \
	esac; \
	\
	url="https://golang.org/dl/go${GOLANG_VERSION}.${goRelArch}.tar.gz"; \
	wget -O go.tgz "$url"; \
	echo "${goRelSha256} *go.tgz" | sha256sum -c -; \
	tar -C /usr/local -xzf go.tgz; \
	rm go.tgz; \
	\
	if [ "$goRelArch" = 'src' ]; then \
		echo >&2; \
		echo >&2 'error: UNIMPLEMENTED'; \
		echo >&2 'TODO install golang-any from jessie-backports for GOROOT_BOOTSTRAP (and uninstall after build)'; \
		echo >&2; \
		exit 1; \
	fi; \
	\
	export PATH="/usr/local/go/bin:$PATH"; \
go version
ENV GOPATH /go
ENV PATH $GOPATH/bin:/usr/local/go/bin:$PATH
RUN go get github.com/prometheus/prom2json/cmd/prom2json
RUN mkdir -p /app
WORKDIR /app
COPY Gemfile /app
COPY *.gemspec /app
COPY ./lib /app/lib
RUN bundle install
COPY . /app
EXPOSE 5400
WORKDIR /app
ENV PUSHGATEWAY_HOST pushgateway
ENV PUSHGATEWAY_PORT 9091
ENV PORT 5400
CMD ["bundle", "exec", "puma", "-C", "config/puma.rb", "-b", "tcp://0.0.0.0:5400"]
