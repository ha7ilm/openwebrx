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
git checkout 0.1.0
python3 setup.py install
popd
rm -rf js8py

git clone https://github.com/jketterl/csdr.git
# latest develop as of 2022-06-01 (locking fixes)
cmakebuild csdr fcb7010f10bfc7456765fc63b64d58f9c5ba0a01

git clone https://github.com/jketterl/pycsdr.git
cd pycsdr
# latest develop as of 2022-06-01 (locking fixes)
git checkout 9753e9a6debb44e7e4d0070a30eb6a8b5ab0c494
./setup.py install install_headers
cd ..
rm -rf pycsdr

git clone https://github.com/jketterl/codecserver.git
mkdir -p /usr/local/etc/codecserver
cp codecserver/conf/codecserver.conf /usr/local/etc/codecserver
# latest develop as of 2022-01-24 (udev)
cmakebuild codecserver 3d9b9a5e1a22407b375bcf8bba316d691d290175

git clone https://github.com/jketterl/digiham.git
# latest develop as of 2021-12-18 (locking fixes)
cmakebuild digiham 4abe335c6119ad8d114fec7dc8262956f8b28feb

git clone https://github.com/jketterl/pydigiham.git
cd pydigiham
# latest develop as of 2021-12-18 (expose library version)
git checkout e0d79a7ef7519ec9e4548288c8c33437913097c5
./setup.py install
cd ..
rm -rf pydigiham

apt-get -y purge --autoremove $BUILD_PACKAGES
apt-get clean
rm -rf /var/lib/apt/lists/*
