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
# latest develop as of 2023-08-15 (rtty and baudot)
cmakebuild csdr 8966688f748d04486560e973a599c26ed4297f34

git clone https://github.com/jketterl/pycsdr.git
cd pycsdr
# latest develop as of 2023-08-15 (rtty and baudot)
git checkout 4e30b6c6a4d73ab4cf99698847c4df68e8206f73
./setup.py install install_headers
cd ..
rm -rf pycsdr

git clone https://github.com/jketterl/codecserver.git
mkdir -p /usr/local/etc/codecserver
cp codecserver/conf/codecserver.conf /usr/local/etc/codecserver
# latest develop as of 2023-07-03 (error handling)
cmakebuild codecserver 0f3703ce285acd85fcd28f6620d7795dc173cb50

git clone https://github.com/jketterl/digiham.git
# latest develop as of 2023-07-02 (codecserver protocol version)
cmakebuild digiham 262e6dfd9a2c56778bd4b597240756ad0fb9861d

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
