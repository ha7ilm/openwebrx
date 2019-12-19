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

STATIC_PACKAGES="sox fftw python3 netcat-openbsd libsndfile lapack libusb qt5-qtbase qt5-qtmultimedia qt5-qtserialport qt5-qttools alsa-lib"
BUILD_PACKAGES="git libsndfile-dev fftw-dev cmake ca-certificates make gcc musl-dev g++ lapack-dev linux-headers autoconf automake libtool texinfo gfortran libusb-dev qt5-qtbase-dev qt5-qtmultimedia-dev qt5-qtserialport-dev qt5-qttools-dev asciidoctor asciidoc alsa-lib-dev linux-headers"

apk add --no-cache $STATIC_PACKAGES
apk add --no-cache --virtual .build-deps $BUILD_PACKAGES

git clone --depth 1 https://git.code.sf.net/p/itpp/git itpp
cmakebuild itpp

git clone --depth 1 https://github.com/jketterl/csdr.git
cd csdr
make
make install
cd ..
rm -rf csdr

git clone --depth 1 https://github.com/szechyjs/mbelib.git
cmakebuild mbelib

git clone --depth 1 https://github.com/jketterl/digiham.git
cmakebuild digiham

git clone --depth 1 https://github.com/f4exb/dsd.git
cmakebuild dsd

WSJT_DIR=wsjtx-2.1.2
WSJT_TGZ=${WSJT_DIR}.tgz
wget http://physics.princeton.edu/pulsar/k1jt/$WSJT_TGZ
tar xvfz $WSJT_TGZ
cmakebuild $WSJT_DIR

git clone --depth 1 https://github.com/wb2osz/direwolf.git
cd direwolf
git checkout 1.5
patch -Np1 < /direwolf-1.5.patch
make
make install
cd ..
rm -rf direwolf

git clone --depth 1 https://github.com/hessu/aprs-symbols /opt/aprs-symbols

apk del .build-deps
