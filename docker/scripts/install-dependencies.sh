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
  cmake ${CMAKE_ARGS:-} ..
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

git clone https://github.com/jketterl/js8py.git
pushd js8py
git checkout 888e62be375316882ad2b2ac8e396c3bf857b6fc
python3 setup.py install
popd

git clone https://git.code.sf.net/p/itpp/git itpp
cmakebuild itpp bb5c7e95f40e8fdb5c3f3d01a84bcbaf76f3676d

git clone https://github.com/jketterl/csdr.git
cd csdr
git checkout 29efbfb961a435fc5d81b0da269deb4a116b3f1c
CSDR_PACKAGE_BUILD=1 make
make install
cd ..
rm -rf csdr

git clone https://github.com/szechyjs/mbelib.git
cmakebuild mbelib 9a04ed5c78176a9965f3d43f7aa1b1f5330e771f

git clone https://github.com/jketterl/digiham.git
cmakebuild digiham 95206501be89b38d0267bf6c29a6898e7c65656f

git clone https://github.com/f4exb/dsd.git
cmakebuild dsd f6939f9edbbc6f66261833616391a4e59cb2b3d7

git clone https://github.com/Hamlib/Hamlib.git
pushd Hamlib
git checkout 301ebb92eaa538dfa75c06821f46715f40dd7673
./bootstrap
./configure
make
make install
popd
rm -rf Hamlib

JS8CALL_VERSION=2.1.1
JS8CALL_DIR=js8call-${JS8CALL_VERSION}
JS8CALL_TGZ=${JS8CALL_DIR}.tgz
wget http://files.js8call.com/${JS8CALL_VERSION}/${JS8CALL_TGZ}
tar xfz ${JS8CALL_TGZ}
CMAKE_ARGS="-D CMAKE_CXX_FLAGS=-DJS8_USE_LEGACY_HAMLIB" cmakebuild ${JS8CALL_DIR}
rm ${JS8CALL_TGZ}

WSJT_DIR=wsjtx-2.1.2
WSJT_TGZ=${WSJT_DIR}.tgz
wget http://physics.princeton.edu/pulsar/k1jt/${WSJT_TGZ}
tar xfz ${WSJT_TGZ}
cmakebuild ${WSJT_DIR}
rm ${WSJT_TGZ}

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
