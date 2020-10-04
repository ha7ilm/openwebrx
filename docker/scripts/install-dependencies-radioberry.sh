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

STATIC_PACKAGES="libusb-1.0-0 libfftw3-3 udev"
BUILD_PACKAGES="git cmake make patch wget sudo gcc g++ libusb-1.0-0-dev libfftw3-dev pkg-config"

apt-get update
apt-get -y install --no-install-recommends $STATIC_PACKAGES $BUILD_PACKAGES

git clone https://github.com/pa3gsb/Radioberry-2.x
cd Radioberry-2.x/SBC/rpi-4

# latest from master as of 2020-09-04
cmakebuild SoapyRadioberrySDR 8d17de6b4dc076e628900a82f05c7cf0b16cbe24
cd ../../..
rm -rf Radioberry-2.x

SUDO_FORCE_REMOVE=yes apt-get -y purge --autoremove $BUILD_PACKAGES
apt-get clean
rm -rf /var/lib/apt/lists/*
