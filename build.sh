#!/bin/bash
set -euxo pipefail

ARCH=$(uname -m)

TAG="latest"
ARCHTAG="$TAG-$ARCH"

docker build --pull -t openwebrx-base:$ARCHTAG -f docker/Dockerfiles/Dockerfile-base .
docker build --build-arg ARCHTAG=$ARCHTAG -t jketterl/openwebrx-rtlsdr:$ARCHTAG -f docker/Dockerfiles/Dockerfile-rtlsdr .
docker build --build-arg ARCHTAG=$ARCHTAG -t openwebrx-soapysdr-base:$ARCHTAG -f docker/Dockerfiles/Dockerfile-soapysdr .
docker build --build-arg ARCHTAG=$ARCHTAG -t jketterl/openwebrx-sdrplay:$ARCHTAG -f docker/Dockerfiles/Dockerfile-sdrplay .
docker build --build-arg ARCHTAG=$ARCHTAG -t jketterl/openwebrx-hackrf:$ARCHTAG -f docker/Dockerfiles/Dockerfile-hackrf .
docker build --build-arg ARCHTAG=$ARCHTAG -t jketterl/openwebrx-airspy:$ARCHTAG -f docker/Dockerfiles/Dockerfile-airspy .
docker build --build-arg ARCHTAG=$ARCHTAG -t jketterl/openwebrx-full:$ARCHTAG -t jketterl/openwebrx:$ARCHTAG -f docker/Dockerfiles/Dockerfile-full .
