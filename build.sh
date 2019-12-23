#!/bin/bash
set -euxo pipefail

ARCH=$(uname -m)

BASE_IMAGE=alpine:3.10

TAGS=$ARCH

docker build --pull --no-cache --build-arg BASE_IMAGE=$BASE_IMAGE -t openwebrx-base:$ARCH -f docker/Dockerfiles/Dockerfile-base .
docker build --build-arg ARCH=$ARCH -t jketterl/openwebrx-rtlsdr:$ARCH -f docker/Dockerfiles/Dockerfile-rtlsdr .
docker build --build-arg ARCH=$ARCH -t openwebrx-soapysdr-base:$ARCH -f docker/Dockerfiles/Dockerfile-soapysdr .
docker build --build-arg ARCH=$ARCH -t jketterl/openwebrx-sdrplay:$ARCH -f docker/Dockerfiles/Dockerfile-sdrplay .
docker build --build-arg ARCH=$ARCH -t jketterl/openwebrx-hackrf:$ARCH -f docker/Dockerfiles/Dockerfile-hackrf .
docker build --build-arg ARCH=$ARCH -t jketterl/openwebrx-airspy:$ARCH -f docker/Dockerfiles/Dockerfile-airspy .
docker build --build-arg ARCH=$ARCH -t jketterl/openwebrx-full:$ARCH -t jketterl/openwebrx:$ARCH -f docker/Dockerfiles/Dockerfile-full .
