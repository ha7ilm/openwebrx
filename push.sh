#!/bin/bash
set -euxo pipefail
. docker/env

for image in ${IMAGES}; do
  docker push jketterl/$image:$ARCHTAG
done