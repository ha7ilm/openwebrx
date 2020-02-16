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

STATIC_PACKAGES="avahi"
BUILD_PACKAGES="git cmake make gcc musl-dev g++ linux-headers avahi-dev"

apk add --no-cache $STATIC_PACKAGES
apk add --no-cache --virtual .build-deps $BUILD_PACKAGES

git clone https://github.com/pothosware/SoapyRemote.git
cmakebuild SoapyRemote 6d9bd820da470cfe7b27b2e6946af93cfece448f

apk del .build-deps
