#!/bin/bash
set -euo pipefail

cd /tmp

BUILD_PACKAGES="git build-essential cmake"

apt-get -y install $BUILD_PACKAGES

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

apt-get -y purge $BUILD_PACKAGES
apt-get -y autoremove

