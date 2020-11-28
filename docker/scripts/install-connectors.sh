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
# latest develop as of 2020-11-28 (c++ refactoring)
cmakebuild owrx_connector 8c7982f1f91bb38f359126725de64a5875221898

apt-get -y purge --autoremove $BUILD_PACKAGES
apt-get clean
rm -rf /var/lib/apt/lists/*
