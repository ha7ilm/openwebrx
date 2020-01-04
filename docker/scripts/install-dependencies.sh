#!/bin/bash
set -euxo pipefail

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

STATIC_PACKAGES="sox fftw python3 netcat-openbsd libsndfile lapack libusb qt5-qtbase qt5-qtmultimedia qt5-qtserialport qt5-qttools alsa-lib"
BUILD_PACKAGES="git libsndfile-dev fftw-dev cmake ca-certificates make gcc musl-dev g++ lapack-dev linux-headers autoconf automake libtool texinfo gfortran libusb-dev qt5-qtbase-dev qt5-qtmultimedia-dev qt5-qtserialport-dev qt5-qttools-dev asciidoctor asciidoc alsa-lib-dev linux-headers"

apk add --no-cache $STATIC_PACKAGES
apk add --no-cache --virtual .build-deps $BUILD_PACKAGES

git clone https://git.code.sf.net/p/itpp/git itpp
cmakebuild itpp bb5c7e95f40e8fdb5c3f3d01a84bcbaf76f3676d

git clone https://github.com/jketterl/csdr.git
cd csdr
git checkout 43c36df5dcd92d3bdb322f9d53f99ca0c7c816a4
make
make install
cd ..
rm -rf csdr

git clone https://github.com/szechyjs/mbelib.git
cmakebuild mbelib 9a04ed5c78176a9965f3d43f7aa1b1f5330e771f

git clone https://github.com/jketterl/digiham.git
cmakebuild digiham 01e1121d7de4d5acdd118c9b4c1c6509535db975

git clone https://github.com/f4exb/dsd.git
cmakebuild dsd f6939f9edbbc6f66261833616391a4e59cb2b3d7

WSJT_DIR=wsjtx-2.1.2
WSJT_TGZ=${WSJT_DIR}.tgz
wget http://physics.princeton.edu/pulsar/k1jt/$WSJT_TGZ
tar xvfz $WSJT_TGZ
cmakebuild $WSJT_DIR

git clone --depth 1 -b 1.5 https://github.com/wb2osz/direwolf.git
cd direwolf
patch -Np1 < /direwolf-1.5.patch
make
make install
cd ..
rm -rf direwolf

git clone https://github.com/hessu/aprs-symbols /opt/aprs-symbols
pushd /opt/aprs-symbols
git checkout 5c2abe2658ee4d2563f3c73b90c6f59124839802
popd

apk del .build-deps
