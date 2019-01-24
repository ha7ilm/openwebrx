#!/bin/bash
set -euxo pipefail

ARCH=$(uname -m)

for image in openwebrx openwebrx-rtlsdr openwebrx-sdrplay; do
  docker push jketterl/$image:$ARCH
done
