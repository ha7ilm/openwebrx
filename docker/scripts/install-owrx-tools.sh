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

STATIC_PACKAGES="libfftw3-bin libprotobuf23 libsamplerate0 libicu67"
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
# latest develop as of 2021-10-25 (deemphasis fix)
cmakebuild csdr b9d65951e0a112677939290a83ee2706cdbeb064

git clone https://github.com/jketterl/pycsdr.git
cd pycsdr
# latest develop as of 2021-09-30 (fft overflow fix)
git checkout 7389af13c87f17844ec67cefa18b922bdc93b14f
./setup.py install install_headers
cd ..
rm -rf pycsdr

git clone https://github.com/jketterl/codecserver.git
mkdir -p /usr/local/etc/codecserver
cp codecserver/conf/codecserver.conf /usr/local/etc/codecserver
# latest develop as of 2021-09-30 (logging fix)
cmakebuild codecserver aa9b1d6057c4461c7f65ec1bbf698a69336bf6df

git clone https://github.com/jketterl/digiham.git
# latest develop as of 2021-12-18 (error handling fixes)
cmakebuild digiham 9dfa1f823e9071f2b048d96121e7f52e9aa9dbac

git clone https://github.com/jketterl/pydigiham.git
cd pydigiham
# latest develop as of 2021-12-18 (error handling fixes)
git checkout 387e7c1591d50aba23801d6a49306fee7d4ebef9
./setup.py install
cd ..
rm -rf pydigiham

apt-get -y purge --autoremove $BUILD_PACKAGES
apt-get clean
rm -rf /var/lib/apt/lists/*
