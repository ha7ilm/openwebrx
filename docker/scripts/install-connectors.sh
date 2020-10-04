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
# this is the latest development version as of 2020-10-04 (ability to build rtl_tcp_connector alone)
cmakebuild owrx_connector ccbf42c78c06c4e1c3e0de6e9ef34fba72a60c75

apt-get -y purge --autoremove $BUILD_PACKAGES
apt-get clean
rm -rf /var/lib/apt/lists/*
