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

STATIC_PACKAGES="libusb-1.0-0"
BUILD_PACKAGES="git cmake make gcc g++ libusb-1.0-0-dev"

apt-get update
apt-get -y install --no-install-recommends $STATIC_PACKAGES $BUILD_PACKAGES

git clone https://github.com/Nuand/bladeRF.git
cmakebuild bladeRF 2023.02

git clone https://github.com/pothosware/SoapyBladeRF.git
# latest from master as of 2023-08-30
cmakebuild SoapyBladeRF 85f6dc554ed4c618304d99395b19c4e1523675b0

apt-get -y purge --autoremove $BUILD_PACKAGES
apt-get clean
rm -rf /var/lib/apt/lists/*
