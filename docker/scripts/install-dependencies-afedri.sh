#!/usr/bin/env bash
set -euo pipefail
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

STATIC_PACKAGES=""
BUILD_PACKAGES="git cmake make gcc g++"

apt-get update
apt-get -y install --no-install-recommends $STATIC_PACKAGES $BUILD_PACKAGES

git clone https://github.com/alexander-sholohov/SoapyAfedri.git
# latest from master as of 2023-11-16
cmakebuild SoapyAfedri a7d0d942fe966c2b69c8817dd6f097fc94122660

apt-get -y purge --autoremove $BUILD_PACKAGES
apt-get clean
rm -rf /var/lib/apt/lists/*
