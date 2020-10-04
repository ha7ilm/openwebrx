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
  cmake ${CMAKE_ARGS:-} ..
  make
  make install
  cd ../..
  rm -rf $1
}

cd /tmp

STATIC_PACKAGES="sox libfftw3-bin python3 python3-setuptools netcat-openbsd libsndfile1 liblapack3 libusb-1.0-0 libqt5core5a libreadline7 libgfortran4 libgomp1 libasound2 libudev1 ca-certificates libqt5gui5 libqt5sql5 libqt5printsupport5 libpulse0 libfaad2 libopus0"
BUILD_PACKAGES="wget git libsndfile1-dev libfftw3-dev cmake make gcc g++ liblapack-dev texinfo gfortran libusb-1.0-0-dev qtbase5-dev qtmultimedia5-dev qttools5-dev libqt5serialport5-dev qttools5-dev-tools asciidoctor asciidoc libasound2-dev libudev-dev libhamlib-dev patch xsltproc qt5-default libfaad-dev libopus-dev"
apt-get update
apt-get -y install auto-apt-proxy
apt-get -y install --no-install-recommends $STATIC_PACKAGES $BUILD_PACKAGES

case `uname -m` in
    arm*)
        PLATFORM=armhf
        ;;
    aarch64*)
        PLATFORM=aarch64
        ;;
    x86_64*)
        PLATFORM=amd64
        ;;
esac

wget https://github.com/just-containers/s6-overlay/releases/download/v1.21.8.0/s6-overlay-${PLATFORM}.tar.gz
tar xzf s6-overlay-${PLATFORM}.tar.gz -C /
rm s6-overlay-${PLATFORM}.tar.gz

git clone https://git.code.sf.net/p/itpp/git itpp
cmakebuild itpp bb5c7e95f40e8fdb5c3f3d01a84bcbaf76f3676d

git clone https://github.com/szechyjs/mbelib.git
cmakebuild mbelib 9a04ed5c78176a9965f3d43f7aa1b1f5330e771f

git clone https://github.com/f4exb/dsd.git
cmakebuild dsd f6939f9edbbc6f66261833616391a4e59cb2b3d7

JS8CALL_VERSION=2.2.0
JS8CALL_DIR=js8call
JS8CALL_TGZ=js8call-${JS8CALL_VERSION}.tgz
wget http://files.js8call.com/${JS8CALL_VERSION}/${JS8CALL_TGZ}
tar xfz ${JS8CALL_TGZ}
# patch allows us to build against the packaged hamlib
patch -Np1 -d ${JS8CALL_DIR} < /js8call-hamlib.patch
rm /js8call-hamlib.patch
CMAKE_ARGS="-D CMAKE_CXX_FLAGS=-DJS8_USE_HAMLIB_THREE" cmakebuild ${JS8CALL_DIR}
rm ${JS8CALL_TGZ}

WSJT_DIR=wsjtx-2.2.2
WSJT_TGZ=${WSJT_DIR}.tgz
wget http://physics.princeton.edu/pulsar/k1jt/${WSJT_TGZ}
tar xfz ${WSJT_TGZ}
patch -Np0 -d ${WSJT_DIR} < /wsjtx-hamlib.patch
mv /wsjtx.patch ${WSJT_DIR}
cmakebuild ${WSJT_DIR}
rm ${WSJT_TGZ}

git clone --depth 1 -b 1.5 https://github.com/wb2osz/direwolf.git
cd direwolf
# hamlib is present (necessary for the wsjt-x and js8call builds) and would be used, but there's no real need.
# by setting enable_hamlib we prevent direwolf from linking to it, and it can be stripped at the end of the script.
make enable_hamlib=
make install
cd ..
rm -rf direwolf
# strip lots of generic documentation that will never be read inside a docker container
rm /usr/local/share/doc/direwolf/*.pdf
# examples are pointless, too
rm -rf /usr/local/share/doc/direwolf/examples/

git clone https://github.com/drowe67/codec2.git
cd codec2
# latest commit from master as of 2020-10-04
git checkout 55d7bb8d1bddf881bdbfcb971a718b83e6344598
mkdir build
cd build
cmake ..
make
make install
install -m 0755 src/freedv_rx /usr/local/bin
cd ../..
rm -rf codec2

wget https://downloads.sourceforge.net/project/drm/dream/2.1.1/dream-2.1.1-svn808.tar.gz
tar xvfz dream-2.1.1-svn808.tar.gz
pushd dream
patch -Np0 < /dream.patch
qmake CONFIG+=console
make
make install
popd
rm -rf dream
rm dream-2.1.1-svn808.tar.gz

git clone https://github.com/hessu/aprs-symbols /opt/aprs-symbols
pushd /opt/aprs-symbols
git checkout 5c2abe2658ee4d2563f3c73b90c6f59124839802
popd

apt-get -y purge --autoremove $BUILD_PACKAGES
apt-get clean
rm -rf /var/lib/apt/lists/*
