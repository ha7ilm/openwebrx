#!/bin/bash
set -euxo pipefail

function cmakebuild() {
  cd $1
  mkdir build
  cd build
  cmake ..
  make 
  sudo make install
  cd ../..
  rm -rf $1
}

cd /tmp

STATIC_PACKAGES="sox libfftw3-dev python2.7 rtl-sdr netcat libitpp-dev libsndfile1-dev libusb-dev"
BUILD_PACKAGES="git build-essential cmake patch"

apt-get update
apt-get -y install --no-install-recommends $STATIC_PACKAGES $BUILD_PACKAGES

wget http://www.sdrplay.com/software/SDRplay_RSP_API-RPi-2.13.1.run 
sh SDRplay_RSP_API-RPi-2.13.1.run --noexec --target sdrplay
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
rm SDRplay_RSP_API-RPi-2.13.1.run

git clone https://github.com/pothosware/SoapySDR
cmakebuild SoapySDR

git clone https://github.com/pothosware/SoapySDRPlay.git
cmakebuild SoapySDRPlay

git clone https://github.com/rxseger/rx_tools
cmakebuild rx_tools

git clone https://github.com/simonyiszk/csdr.git
cd csdr
make
make install
cd ..
rm -rf csdr

git clone https://github.com/szechyjs/mbelib.git
cmakebuild mbelib

git clone https://github.com/jketterl/digiham.git
cmakebuild digiham

git clone https://github.com/szechyjs/dsd.git
cmakebuild dsd

apt-get remove --purge --autoremove -y $BUILD_PACKAGES
rm -rf /var/lib/apt/lists/*

