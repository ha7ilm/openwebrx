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

BUILD_PACKAGES="git cmake make gcc g++ musl-dev"

apk add --no-cache --virtual .build-deps $BUILD_PACKAGES


git clone https://github.com/jketterl/owrx_connector.git
cmakebuild owrx_connector b68210e59b8475ed3dfc4dfb25de0b0a63193b87

apk del .build-deps
