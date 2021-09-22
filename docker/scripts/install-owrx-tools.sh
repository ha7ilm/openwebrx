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

STATIC_PACKAGES="libfftw3-bin libprotobuf17 libsamplerate0 libicu63"
BUILD_PACKAGES="git autoconf automake libtool libfftw3-dev pkg-config cmake make gcc g++ libprotobuf-dev protobuf-compiler libsamplerate-dev libicu-dev libpython3-dev"
apt-get update
apt-get -y install --no-install-recommends $STATIC_PACKAGES $BUILD_PACKAGES

git clone https://github.com/jketterl/js8py.git
pushd js8py
git checkout 0.1.0
python3 setup.py install
popd
rm -rf js8py

git clone https://github.com/jketterl/csdr.git
# latest develop as of 2021-09-22 (template fixes)
cmakebuild csdr 536f3b9eb7cfe5434e9a9f1e807c96115dc9ac10

git clone https://github.com/jketterl/pycsdr.git
cd pycsdr
# latest develop as of 2021-09-22 (first version)
git checkout 52da48a87ef97eb7d337f1b146db66ca453801e4
./setup.py install install_headers
cd ..
rm -rf pycsdr

git clone https://github.com/jketterl/codecserver.git
mkdir -p /usr/local/etc/codecserver
cp codecserver/conf/codecserver.conf /usr/local/etc/codecserver
cmakebuild codecserver 0.1.0

git clone https://github.com/jketterl/digiham.git
# latest develop as of 2021-09-22 (post-merge)
cmakebuild digiham 62d2b4581025568263ae8c90d2450b65561b7ce8

git clone https://github.com/jketterl/pydigiham.git
cd pydigiham
# latest develop as of 2021-09-22 (split from digiham)
git checkout b0cc0c35d5ef2ae84c9bb1a02d56161d5bd5bf2f
./setup.py install
cd ..
rm -rf pydigiham

apt-get -y purge --autoremove $BUILD_PACKAGES
apt-get clean
rm -rf /var/lib/apt/lists/*
