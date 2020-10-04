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

git clone https://github.com/mossmann/hackrf.git
cd hackrf
# latest from master as of 2020-09-04
git checkout 6e5cbda2945c3bab0e6e1510eae418eda60c358e
cmakebuild host
cd ..
rm -rf hackrf

git clone https://github.com/pothosware/SoapyHackRF.git
# latest from master as of 2020-09-04
cmakebuild SoapyHackRF 7d530872f96c1cbe0ed62617c32c48ce7e103e1d

SUDO_FORCE_REMOVE=yes apt-get -y purge --autoremove $BUILD_PACKAGES
apt-get clean
rm -rf /var/lib/apt/lists/*
