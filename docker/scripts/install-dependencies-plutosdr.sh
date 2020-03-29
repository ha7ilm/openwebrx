#!/usr/bin/env bash
set -euo pipefail
export MAKEFLAGS="-j4"

function cmakebuild() {
  cd $1
  if [[ ! -z "${2:-}" ]]; then
    git checkout $2
  fi
  mkdir build
  cd build
  cmake .. ${3:-}
  make
  make install
  cd ../..
  rm -rf $1
}

cd /tmp

STATIC_PACKAGES="libusb libxml2"
BUILD_PACKAGES="git libusb-dev cmake make gcc musl-dev g++ linux-headers libxml2-dev flex bison"

apk add --no-cache $STATIC_PACKAGES
apk add --no-cache --virtual .build-deps $BUILD_PACKAGES

git clone https://github.com/analogdevicesinc/libiio.git
cmakebuild libiio 5f5af2e417129ad8f4e05fc5c1b730f0694dca12 -DCMAKE_INSTALL_PREFIX=/usr/local

git clone https://github.com/analogdevicesinc/libad9361-iio.git
cmakebuild libad9361-iio 8ac95f3325c18c2e34cd9cfd49c7b63d69a0a9d2

git clone https://github.com/pothosware/SoapyPlutoSDR.git
cmakebuild SoapyPlutoSDR c88b7f5bac1e5785f212f9a7c6ce8fef64eb719e

apk del .build-deps
