#!/bin/sh
rm -rf pool
rm -rf dists
mkdir -p pool/RO
mv .build/*.deb pool/RO/
mkdir -p dists/unstable/RO/binary-amd64/
apt-ftparchive packages pool/RO > dists/unstable/RO/binary-amd64/Packages
gzip -9fk dists/unstable/RO/binary-amd64/Packages
