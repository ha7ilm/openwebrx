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

STATIC_PACKAGES="libusb"
BUILD_PACKAGES="git cmake make patch wget sudo udev gcc g++ libusb-dev"

apk add --no-cache $STATIC_PACKAGES
apk add --no-cache --virtual .build-deps $BUILD_PACKAGES

case $(arch) in
  x86_64)
    BINARY=SDRplay_RSP_API-Linux-2.13.1.run
    ;;
  armv*)
    BINARY=SDRplay_RSP_API-RPi-2.13.1.run
    ;;
esac

wget http://www.sdrplay.com/software/$BINARY
sh $BINARY --noexec --target sdrplay
patch -Np0 <<'EOF'
--- sdrplay/install_lib.sh	2018-06-20 23:57:02.000000000 +0000
+++ sdrplay/install_lib_patched.sh	2019-01-13 17:52:56.723838354 +0000
@@ -2,18 +2,6 @@
 
 echo "Installing SDRplay RSP API library 2.13..."
 
-more sdrplay_license.txt
-
-while true; do
-    echo "Press y and RETURN to accept the license agreement and continue with"
-    read -p "the installation, or press n and RETURN to exit the installer [y/n] " yn
-    case $yn in
-        [Yy]* ) break;;
-        [Nn]* ) exit;;
-        * ) echo "Please answer y or n";;
-    esac
-done
-
 export ARCH=`arch`
 export VERS="2.13"
 
EOF
cd sdrplay
./install_lib.sh
cd ..
rm -rf sdrplay
rm $BINARY

git clone https://github.com/pothosware/SoapySDR
cmakebuild SoapySDR

git clone https://github.com/pothosware/SoapySDRPlay.git
cmakebuild SoapySDRPlay

git clone https://github.com/rxseger/rx_tools
cmakebuild rx_tools

apk del .build-deps
