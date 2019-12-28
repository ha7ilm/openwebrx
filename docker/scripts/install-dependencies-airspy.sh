#!/bin/bash
set -euxo pipefail

function cmakebuild() {
  cd $1
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

git clone --depth 1 https://github.com/airspy/airspyone_host.git
cmakebuild airspyone_host

git clone --depth 1 https://github.com/pothosware/SoapyAirspy.git
cmakebuild SoapyAirspy

git clone --depth 1 https://github.com/airspy/airspyhf.git
cmakebuild airspyhf

git clone --depth 1 https://github.com/pothosware/SoapyAirspyHF.git
cmakebuild SoapyAirspyHF

apk del .build-deps
