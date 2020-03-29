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

git clone https://github.com/osmocom/rtl-sdr.git
cmakebuild rtl-sdr d794155ba65796a76cd0a436f9709f4601509320

git clone https://github.com/pothosware/SoapyRTLSDR.git
cmakebuild SoapyRTLSDR 8ba18f17d64005e43ff2a4e46611f8c710b05007

apk del .build-deps
