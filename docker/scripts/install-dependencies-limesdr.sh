#!/usr/bin/env bash
set -euo pipefail
export MAKEFLAGS="-j4"

cd /tmp

STATIC_PACKAGES="libusb"
BUILD_PACKAGES="git libusb-dev cmake make gcc musl-dev g++ linux-headers"

apk add --no-cache $STATIC_PACKAGES
apk add --no-cache --virtual .build-deps $BUILD_PACKAGES

git clone https://github.com/myriadrf/LimeSuite.git
cd LimeSuite
git checkout 1c1c202f9a6ae4bb34068b6f3f576f7f8e74c7f1
mkdir builddir
cd builddir
cmake .. -DENABLE_EXAMPLES=OFF -DENABLE_DESKTOP=OFF -DENABLE_LIME_UTIL=OFF -DENABLE_QUICKTEST=OFF -DENABLE_OCTAVE=OFF -DENABLE_GUI=OFF -DCMAKE_CXX_STANDARD_LIBRARIES="-latomic"
make
make install
cd ../..
rm -rf LimeSuite

apk del .build-deps
