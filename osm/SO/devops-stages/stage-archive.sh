#!/bin/sh
rm -rf pool
rm -rf dists
mkdir -p pool/SO
mv .build/*.deb pool/SO/
mkdir -p dists/unstable/SO/binary-amd64/
apt-ftparchive packages pool/SO > dists/unstable/SO/binary-amd64/Packages
gzip -9fk dists/unstable/SO/binary-amd64/Packages
