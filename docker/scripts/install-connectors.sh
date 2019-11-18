#!/usr/bin/env bash
set -euxo pipefail

function cmakebuild() {
  cd $1
  mkdir build
  cd build
  cmake ..
  make
  make install
  cd ../..
  rm -rf $1
}

cd /tmp

BUILD_PACKAGES="git cmake make gcc g++ musl-dev"

apk add --no-cache --virtual .build-deps $BUILD_PACKAGES


git clone https://github.com/jketterl/owrx_connector.git
cmakebuild owrx_connector

apk del .build-deps
