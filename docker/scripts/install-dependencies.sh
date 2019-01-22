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

STATIC_PACKAGES="sox libfftw3-dev python2.7 netcat libitpp-dev libsndfile1-dev"
BUILD_PACKAGES="git build-essential cmake ca-certificates"

apt-get update
apt-get -y install --no-install-recommends $STATIC_PACKAGES $BUILD_PACKAGES

git clone https://github.com/simonyiszk/csdr.git
cd csdr
make
make install
cd ..
rm -rf csdr

git clone https://github.com/szechyjs/mbelib.git
cmakebuild mbelib

git clone https://github.com/jketterl/digiham.git
cmakebuild digiham

git clone https://github.com/f4exb/dsd.git
cmakebuild dsd

apt-get remove --purge --autoremove -y $BUILD_PACKAGES
rm -rf /var/lib/apt/lists/*

