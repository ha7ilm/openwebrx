#!/usr/bin/env bash
set -euxo pipefail
export MAKEFLAGS="-j4"

cd /tmp

STATIC_PACKAGES="libusb udev"
BUILD_PACKAGES="git make gcc autoconf automake libtool musl-dev libusb-dev shadow vim"

apk add --no-cache $STATIC_PACKAGES
apk add --no-cache --virtual .build-deps $BUILD_PACKAGES

git clone https://github.com/Microtelecom/libperseus-sdr.git
cd libperseus-sdr
git checkout 72ac67c5b7936a1991be0ec97c03a59c1a8ac8f3
./bootstrap.sh
./configure
make
make install
ldconfig /etc/ld.so.conf.d
cd ..
rm -rf libperseus-sdr

apk del .build-deps
