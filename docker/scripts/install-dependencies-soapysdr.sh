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
  cmake ..
  make
  make install
  cd ../..
  rm -rf $1
}

cd /tmp

STATIC_PACKAGES="udev"
BUILD_PACKAGES="git cmake make patch wget sudo gcc g++"

apk add --no-cache $STATIC_PACKAGES
apk add --no-cache --virtual .build-deps $BUILD_PACKAGES

git clone https://github.com/pothosware/SoapySDR
cmakebuild SoapySDR f722f9ce5b629c3c44401a9bf628b3f8e67a9695

apk del .build-deps
