#!/usr/bin/env bash
set -euo pipefail

function cmakebuild() {
  cd $1
  if [[ ! -z "${2:-}" ]]; then
    git checkout $2
  fi
  mkdir build
  cd build
  cmake ..
  make
  make install
  cd ../..
  rm -rf $1
}

cd /tmp

STATIC_PACKAGES="libusb"
BUILD_PACKAGES="git libusb-dev cmake make gcc musl-dev g++ linux-headers"

apk add --no-cache $STATIC_PACKAGES
apk add --no-cache --virtual .build-deps $BUILD_PACKAGES

git clone https://github.com/analogdevicesinc/libiio.git
cmakebuild libiio 4e22517c60f3c5e691320871956edede15459ae3

git clone https://github.com/analogdevicesinc/libad9361-iio.git
cmakebuild libad9361-iio 8ac95f3325c18c2e34cd9cfd49c7b63d69a0a9d2

git clone https://github.com/pothosware/SoapyPlutoSDR.git
cmakebuild SoapyPlutoSDR e28e4f5c68c16a38c0b50b9606035f3267a135c8

apk del .build-deps
