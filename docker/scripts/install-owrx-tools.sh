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

STATIC_PACKAGES="libfftw3-bin"
BUILD_PACKAGES="git autoconf automake libtool libfftw3-dev pkg-config cmake make gcc g++"
apt-get update
apt-get -y install --no-install-recommends $STATIC_PACKAGES $BUILD_PACKAGES

git clone https://github.com/jketterl/js8py.git
pushd js8py
git checkout 888e62be375316882ad2b2ac8e396c3bf857b6fc
python3 setup.py install
popd
rm -rf js8py

git clone https://github.com/jketterl/csdr.git
cd csdr
# develop as of 2020-09-06 (fractional_decimator_cc pointer fix)
git checkout f123f81add2f84e3ada66d66afd53cf96b7fec94
autoreconf -i
./configure
make
make install
cd ..
rm -rf csdr

git clone https://github.com/jketterl/digiham.git
cmakebuild digiham 95206501be89b38d0267bf6c29a6898e7c65656f

apt-get -y purge --autoremove $BUILD_PACKAGES
apt-get clean
rm -rf /var/lib/apt/lists/*
