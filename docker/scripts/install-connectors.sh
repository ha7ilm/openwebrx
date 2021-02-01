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

BUILD_PACKAGES="git cmake make gcc g++"

apt-get update
apt-get -y install --no-install-recommends $BUILD_PACKAGES

git clone https://github.com/jketterl/owrx_connector.git
# latest develop as of 2021-02-01 (string parsing fixes)
cmakebuild owrx_connector 4789a82015a66f11440bdfd4a935bafa7da22fbe

apt-get -y purge --autoremove $BUILD_PACKAGES
apt-get clean
rm -rf /var/lib/apt/lists/*
