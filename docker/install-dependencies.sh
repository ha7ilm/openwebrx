#!/bin/bash
set -euxo pipefail

cd /tmp

STATIC_PACKAGES="sox libfftw3-dev python2.7 rtl-sdr netcat libitpp-dev libsndfile1-dev"
BUILD_PACKAGES="git build-essential cmake"

apt-get update
apt-get -y install --no-install-recommends $STATIC_PACKAGES $BUILD_PACKAGES

git clone https://github.com/simonyiszk/csdr.git
cd csdr
make
make install
cd ..
rm -rf csdr

git clone https://github.com/szechyjs/mbelib.git
cd mbelib
mkdir build
cd build
cmake ..
make
make install
cd ../..
rm -rf mbelib
    
git clone https://github.com/jketterl/digiham.git
cd digiham
mkdir build
cd build
cmake ..
make
make install
cd ../..
rm -rf digiham

git clone https://github.com/szechyjs/dsd.git
cd dsd
mkdir build
cd build
cmake ..
make
make install
cd ../..
rm -rf dsd

apt-get remove --purge --autoremove -y $BUILD_PACKAGES
rm -rf /var/lib/apt/lists/*

