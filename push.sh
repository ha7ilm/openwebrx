#!/bin/bash
set -euxo pipefail

ARCH=$(uname -m)

ALL_ARCHS="x86_64 armv7l"

for image in openwebrx-rtlsdr openwebrx-sdrplay openwebrx-hackrf openwebrx-airspy openwebrx-full openwebrx; do
  docker push jketterl/$image:$ARCH
  IMAGE_LIST=""
  for a in $ALL_ARCHS; do
    IMAGE_LIST="$IMAGE_LIST jketterl/$image:$a"
  done
  docker manifest create --amend jketterl/$image:latest $IMAGE_LIST
  docker manifest push jketterl/$image:latest
done
