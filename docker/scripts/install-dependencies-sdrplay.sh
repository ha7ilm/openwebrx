#!/bin/bash
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

STATIC_PACKAGES="libusb udev"
BUILD_PACKAGES="git cmake make patch wget sudo gcc g++ libusb-dev"

apk add --no-cache $STATIC_PACKAGES
apk add --no-cache --virtual .build-deps $BUILD_PACKAGES

ARCH=$(uname -m)

case $ARCH in
  x86_64)
    BINARY=SDRplay_RSP_API-Linux-2.13.1.run
    ;;
  armv*)
    BINARY=SDRplay_RSP_API-RPi-2.13.1.run
    ;;
esac

wget http://www.sdrplay.com/software/$BINARY
sh $BINARY --noexec --target sdrplay
patch --verbose -Np0 < /install-lib.$ARCH.patch

cd sdrplay
./install_lib.sh
cd ..
rm -rf sdrplay
rm $BINARY

git clone https://github.com/pothosware/SoapySDRPlay.git
cmakebuild SoapySDRPlay

apk del .build-deps
