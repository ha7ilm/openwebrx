#!/bin/bash
set -euxo pipefail

ARCH=$(uname -m)

case $ARCH in
  x86_64)
    BASE_IMAGE=alpine
    ;;
  armv*)
    BASE_IMAGE=arm32v6/alpine
esac

TAGS=$ARCH

docker build --pull --build-arg BASE_IMAGE=$BASE_IMAGE -t openwebrx-base:$ARCH -f docker/Dockerfiles/Dockerfile-base .
docker build --build-arg ARCH=$ARCH -t jketterl/openwebrx-rtlsdr:$ARCH -f docker/Dockerfiles/Dockerfile-rtlsdr .
docker build --build-arg ARCH=$ARCH -t openwebrx-soapysdr-base:$ARCH -f docker/Dockerfiles/Dockerfile-soapysdr .
docker build --build-arg ARCH=$ARCH -t jketterl/openwebrx-sdrplay:$ARCH -f docker/Dockerfiles/Dockerfile-sdrplay .
docker build --build-arg ARCH=$ARCH -t jketterl/openwebrx-hackrf:$ARCH -f docker/Dockerfiles/Dockerfile-hackrf .
docker build --build-arg ARCH=$ARCH -t jketterl/openwebrx-airspy:$ARCH -f docker/Dockerfiles/Dockerfile-airspy .
docker build --build-arg ARCH=$ARCH -t jketterl/openwebrx-full:$ARCH -t jketterl/openwebrx:$ARCH -f docker/Dockerfiles/Dockerfile-full .
