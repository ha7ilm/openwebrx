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

STATIC_PACKAGES="libfftw3-bin libprotobuf23 libsamplerate0 libicu67 libudev1"
BUILD_PACKAGES="git autoconf automake libtool libfftw3-dev pkg-config cmake make gcc g++ libprotobuf-dev protobuf-compiler libsamplerate-dev libicu-dev libpython3-dev libudev-dev"
apt-get update
apt-get -y install --no-install-recommends $STATIC_PACKAGES $BUILD_PACKAGES

git clone https://github.com/jketterl/js8py.git
pushd js8py
# latest develop as of 2022-11-30 (structured callsign data)
git checkout f7e394b7892d26cbdcce5d43c0b4081a2a6a48f6
python3 setup.py install
popd
rm -rf js8py

git clone https://github.com/jketterl/csdr.git
# latest develop as of 2023-06-30 (csdr cleanup)
cmakebuild csdr 7e7a7f27b9fd1a65d4a9d0725583dfe6309a5245

git clone https://github.com/jketterl/pycsdr.git
cd pycsdr
# latest develop as of 2023-06-30 (csdr cleanup)
git checkout be8b0e5e0b972ebb302e7397bac0058f620ec374
./setup.py install install_headers
cd ..
rm -rf pycsdr

git clone https://github.com/jketterl/codecserver.git
mkdir -p /usr/local/etc/codecserver
cp codecserver/conf/codecserver.conf /usr/local/etc/codecserver
cmakebuild codecserver 0.2.0

git clone https://github.com/jketterl/digiham.git
# latest develop as of 2023-06-30 (csdr cleanup)
cmakebuild digiham ebb97eba8bff58a1d7b0e9f29f9a066e4a91da3d

git clone https://github.com/jketterl/pydigiham.git
cd pydigiham
# latest develop as of 2023-06-30 (csdr cleanup)
git checkout 894aa87ea9a3534d1e7109da86194c7cd5e0b7c7
./setup.py install
cd ..
rm -rf pydigiham

apt-get -y purge --autoremove $BUILD_PACKAGES
apt-get clean
rm -rf /var/lib/apt/lists/*
