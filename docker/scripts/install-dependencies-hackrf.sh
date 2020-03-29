#!/bin/bash
set -euxo pipefail
export MAKEFLAGS="-j4"

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

STATIC_PACKAGES="libusb fftw udev"
BUILD_PACKAGES="git cmake make patch wget sudo gcc g++ libusb-dev fftw-dev"

apk add --no-cache $STATIC_PACKAGES
apk add --no-cache --virtual .build-deps $BUILD_PACKAGES

git clone https://github.com/mossmann/hackrf.git
cd hackrf
git checkout 43e6f99fe8543094d18ff3a6550ed2066c398862
cmakebuild host
cd ..
rm -rf hackrf

apk del .build-deps
