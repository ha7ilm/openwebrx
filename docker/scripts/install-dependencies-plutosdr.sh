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

STATIC_PACKAGES="libusb-1.0-0 libxml2"
BUILD_PACKAGES="git libusb-1.0-0-dev cmake make gcc g++ libxml2-dev flex bison pkg-config"

apt-get update
apt-get -y install --no-install-recommends $STATIC_PACKAGES $BUILD_PACKAGES

git clone https://github.com/analogdevicesinc/libiio.git
cmakebuild libiio v0.21 -DCMAKE_INSTALL_PREFIX=/usr/local

git clone https://github.com/analogdevicesinc/libad9361-iio.git
cmakebuild libad9361-iio v0.2

git clone https://github.com/pothosware/SoapyPlutoSDR.git
# latest from master as of 2020-09-04
cmakebuild SoapyPlutoSDR 93717b32ef052e0dfa717aa2c1a4eb27af16111f

apt-get -y purge --autoremove $BUILD_PACKAGES
apt-get clean
rm -rf /var/lib/apt/lists/*
