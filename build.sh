#!/bin/bash
set -euxo pipefail

ARCH=$(uname -m)

case $ARCH in
  x86_64)
    BASE_IMAGE=debian:stretch
    ;;
  armv*)
    BASE_IMAGE=arm32v6/alpine
esac

TAGS=$ARCH

docker build --build-arg BASE_IMAGE=$BASE_IMAGE -t openwebrx-base:$ARCH -f docker/Dockerfiles/Dockerfile-base .
docker build --build-arg ARCH=$ARCH -t jketterl/openwebrx-rtlsdr:$ARCH -t jketterl/openwebrx:$ARCH -f docker/Dockerfiles/Dockerfile-rtlsdr .
docker build --build-arg ARCH=$ARCH -t jketterl/openwebrx-sdrplay:$ARCH -f docker/Dockerfiles/Dockerfile-sdrplay .

if [ "$ARCH" == "armv7l" ]; then
  for image in openwebrx openwebrx-rtlsdr openwebrx-sdrplay; do
    docker tag jketterl/$image:$ARCH jketterl/$image:latest
  done
fi
