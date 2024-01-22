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

STATIC_PACKAGES="libfftw3-single3 libprotobuf32 libsamplerate0 libicu72 libudev1"
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
# latest develop as of 2024-01-22 (downmix format)
cmakebuild csdr e6ae546a6a1d3fd052fe962eb5a04fd33e794214

git clone https://github.com/jketterl/pycsdr.git
cd pycsdr
# latest develop as of 2024-01-22 (downmix format)
git checkout c7dafe83d08b74012e233502dff0bc6e6f17c01c
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
