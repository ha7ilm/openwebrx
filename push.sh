#!/bin/bash
set -euxo pipefail

ARCH=$(uname -m)

ALL_ARCHS="x86_64 armv7l aarch64"
TAG="latest"
ARCHTAG="$TAG-$ARCH"

IMAGES="openwebrx-rtlsdr openwebrx-sdrplay openwebrx-hackrf openwebrx-airspy openwebrx-rtlsdr-soapy openwebrx-plutosdr openwebrx-limesdr openwebrx-full openwebrx"

for image in ${IMAGES}; do
  docker push jketterl/$image:$ARCHTAG
done

for image in ${IMAGES}; do
  # there's no docker manifest rm command, and the create --amend does not work, so we have to clean up manually
  rm -rf "${HOME}/.docker/manifests/docker.io_jketterl_${image}-${TAG}"
  IMAGE_LIST=""
  for a in $ALL_ARCHS; do
    IMAGE_LIST="$IMAGE_LIST jketterl/$image:$TAG-$a"
  done
  docker manifest create jketterl/$image:$TAG $IMAGE_LIST
  docker manifest push --purge jketterl/$image:$TAG
  docker pull jketterl/$image:$TAG
done
