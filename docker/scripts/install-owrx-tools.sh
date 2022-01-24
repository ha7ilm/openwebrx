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
# latest develop as of 2022-01-24 (additional ring buffer types)
cmakebuild csdr 0e74db2e3b021b192bdf9b8afbbf20102c1c57fe

git clone https://github.com/jketterl/pycsdr.git
cd pycsdr
# latest develop as of 2022-01-24 (added buffer resume())
git checkout e8213fe257467ef7bfe91d1e09b6a2173e55c804
./setup.py install install_headers
cd ..
rm -rf pycsdr

git clone https://github.com/jketterl/codecserver.git
mkdir -p /usr/local/etc/codecserver
cp codecserver/conf/codecserver.conf /usr/local/etc/codecserver
# latest develop as of 2022-01-24 (udev)
cmakebuild codecserver 3d9b9a5e1a22407b375bcf8bba316d691d290175

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
