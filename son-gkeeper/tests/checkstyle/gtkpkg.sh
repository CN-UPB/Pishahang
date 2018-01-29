#!/bin/bash
docker run -i --rm=true -v "$(pwd)/reports:/app/reports/" registry.sonata-nfv.eu:5000/son-gtkpkg bundle exec rubocop --require rubocop/formatter/checkstyle_formatter --format RuboCop::Formatter::CheckstyleFormatter --no-color --out reports/checkstyle-gtkpkg.xml --format html -o reports/index-gtkpkg.html || true
