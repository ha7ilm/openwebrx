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
BUILD_PACKAGES="git libusb-1.0-0-dev cmake make gcc g++ pkg-config"

apt-get update
apt-get -y install --no-install-recommends $STATIC_PACKAGES $BUILD_PACKAGES

git clone https://github.com/airspy/airspyone_host.git
# latest from master as of 2020-09-04
cmakebuild airspyone_host 652fd7f1a8f85687641e0bd91f739694d7258ecc

git clone https://github.com/pothosware/SoapyAirspy.git
cmakebuild SoapyAirspy 10d697b209e7f1acc8b2c8d24851d46170ef77e3

git clone https://github.com/airspy/airspyhf.git
# latest from master as of 2020-09-04
cmakebuild airspyhf 8891387edddcd185e2949e9814e9ef35f46f0722

git clone https://github.com/pothosware/SoapyAirspyHF.git
# latest from master as of 2020-09-04
cmakebuild SoapyAirspyHF 5488dac5b44f1432ce67b40b915f7e61d3bd4853

apt-get -y purge --autoremove $BUILD_PACKAGES
apt-get clean
rm -rf /var/lib/apt/lists/*
