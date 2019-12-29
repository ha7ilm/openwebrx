#!/usr/bin/env bash
set -euxo pipefail

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
cmakebuild owrx_connector 1a1a8615b4d92827d93d3135556e44b7b0bbc98f

apk del .build-deps
