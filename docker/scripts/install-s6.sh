#!/usr/bin/env bash
set -eux pipefail

BUILD_PACKAGES="wget ca-certificates"

apt-get update
apt-get -y install --no-install-recommends $BUILD_PACKAGES

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

pushd /tmp
wget https://github.com/just-containers/s6-overlay/releases/download/v1.21.8.0/s6-overlay-${PLATFORM}.tar.gz
tar xzf s6-overlay-${PLATFORM}.tar.gz -C /
rm s6-overlay-${PLATFORM}.tar.gz
popd

apt-get -y purge --autoremove $BUILD_PACKAGES
apt-get clean
rm -rf /var/lib/apt/lists/*
