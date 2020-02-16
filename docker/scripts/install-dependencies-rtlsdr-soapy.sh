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
cmakebuild rtl-sdr b5af355b1d833b3c898a61cf1e072b59b0ea3440

git clone https://github.com/pothosware/SoapyRTLSDR.git
cmakebuild SoapyRTLSDR 5c5d9503337c6d1c34b496dec6f908aab9478b0f

apk del .build-deps
