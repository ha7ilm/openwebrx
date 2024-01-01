#!/usr/bin/env bash
set -euxo pipefail
export MAKEFLAGS="-j4"

function cmakebuild() {
  cd $1
  if [[ ! -z "${2:-}" ]]; then
    git checkout $2
  fi
  mkdir build
  cd build
  cmake ..
  make
  make install
  cd ../..
  rm -rf $1
}

cd /tmp

STATIC_PACKAGES="libfftw3-single3"
BUILD_PACKAGES="git cmake make gcc g++ libsamplerate-dev libfftw3-dev"

apt-get update
apt-get -y install --no-install-recommends $STATIC_PACKAGES $BUILD_PACKAGES

git clone https://github.com/jketterl/owrx_connector.git
# latest develop as of 2024-01-01 (fixed startup race condition)
cmakebuild owrx_connector 62219d40e180abb539ad61fcd9625b90c34f0e26

apt-get -y purge --autoremove $BUILD_PACKAGES
apt-get clean
rm -rf /var/lib/apt/lists/*
