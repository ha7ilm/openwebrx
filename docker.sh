#!/usr/bin/env bash
set -euo pipefail

ARCH=$(uname -m)
IMAGES="openwebrx-rtlsdr openwebrx-sdrplay openwebrx-hackrf openwebrx-airspy openwebrx-afedri openwebrx-rtlsdr-soapy openwebrx-plutosdr openwebrx-limesdr openwebrx-soapyremote openwebrx-perseus openwebrx-fcdpp openwebrx-radioberry openwebrx-uhd openwebrx-rtltcp openwebrx-runds openwebrx-hpsdr openwebrx-bladerf openwebrx-full openwebrx"
ALL_ARCHS="x86_64 armv7l aarch64"
TAG=${TAG:-"latest"}
ARCHTAG="${TAG}-${ARCH}"

usage () {
  echo "Usage: ${0} [command]"
  echo "Available commands:"
  echo "  help       Show this usage information"
  echo "  build      Build all docker images"
  echo "  push       Push built docker images to the docker hub"
  echo "  manifest   Compile the docker hub manifest (combines arm and x86 tags into one)"
  echo "  tag        Tag a release"
}

build () {
  # build the base images
  docker build --pull -t openwebrx-base:${ARCHTAG} -f docker/Dockerfiles/Dockerfile-base .
  docker build --build-arg ARCHTAG=${ARCHTAG} -t openwebrx-soapysdr-base:${ARCHTAG} -f docker/Dockerfiles/Dockerfile-soapysdr .

  for image in ${IMAGES}; do
    i=${image:10}
    # "openwebrx" is a special image that gets tag-aliased later on
    if [[ ! -z "${i}" ]] ; then
      docker build --build-arg ARCHTAG=$ARCHTAG -t jketterl/${image}:${ARCHTAG} -f docker/Dockerfiles/Dockerfile-${i} .
    fi
  done

  # tag openwebrx alias image
  docker tag jketterl/openwebrx-full:${ARCHTAG} jketterl/openwebrx:${ARCHTAG}
}

push () {
  for image in ${IMAGES}; do
    docker push jketterl/${image}:${ARCHTAG}
  done
}

manifest () {
  for image in ${IMAGES}; do
    # there's no docker manifest rm command, and the create --amend does not work, so we have to clean up manually
    rm -rf "${HOME}/.docker/manifests/docker.io_jketterl_${image}-${TAG}"
    IMAGE_LIST=""
    for a in ${ALL_ARCHS}; do
      IMAGE_LIST="${IMAGE_LIST} jketterl/${image}:${TAG}-${a}"
    done
    docker manifest create jketterl/${image}:${TAG} ${IMAGE_LIST}
    docker manifest push --purge jketterl/${image}:${TAG}
  done
}

tag () {
  if [[ -x ${1:-} || -z ${2:-} ]] ; then
    echo "Usage: ${0} tag [SRC_TAG] [TARGET_TAG]"
    return
  fi

  local SRC_TAG=${1}
  local TARGET_TAG=${2}

  for image in ${IMAGES}; do
    # there's no docker manifest rm command, and the create --amend does not work, so we have to clean up manually
    rm -rf "${HOME}/.docker/manifests/docker.io_jketterl_${image}-${TARGET_TAG}"
    IMAGE_LIST=""
    for a in ${ALL_ARCHS}; do
      docker pull jketterl/${image}:${SRC_TAG}-${a}
      docker tag jketterl/${image}:${SRC_TAG}-${a} jketterl/${image}:${TARGET_TAG}-${a}
      docker push jketterl/${image}:${TARGET_TAG}-${a}
      IMAGE_LIST="${IMAGE_LIST} jketterl/${image}:${TARGET_TAG}-${a}"
    done
    docker manifest create jketterl/${image}:${TARGET_TAG} ${IMAGE_LIST}
    docker manifest push --purge jketterl/${image}:${TARGET_TAG}
    docker pull jketterl/${image}:${TARGET_TAG}
  done
}

case ${1:-} in
  build)
    build
    ;;
  push)
    push
    ;;
  manifest)
    manifest
    ;;
  tag)
    tag ${@:2}
    ;;
  *)
    usage
    ;;
esac