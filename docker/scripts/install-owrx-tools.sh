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
# latest develop as of 2024-01-25 (exemodule setargs)
cmakebuild csdr 344179a616cdbadf501479ce9ed1b836543e657b

git clone https://github.com/jketterl/pycsdr.git
cd pycsdr
# latest develop as of 2024-01-25 (execmodule setargs)
git checkout 9063b8a119e366c31d089596641a24a427e3cbdc
./setup.py install install_headers
cd ..
rm -rf pycsdr

git clone https://github.com/jketterl/csdr-eti.git
# latest develop as of 2024-01-26 (global variables fix)
cmakebuild csdr-eti 9f2360e7ab080d3a9da5e04978c260cc911c06ca

git clone https://github.com/jketterl/pycsdr-eti.git
cd pycsdr-eti
# latest develop as of 2024-01-26 (initial integration)
git checkout ebc29af1eb7c0be7532c91cf459f064dcb017455
./setup.py install
cd ..
rm -rf pycsdr-eti

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
