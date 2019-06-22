#!/bin/bash
set -euxo pipefail

ARCH=$(uname -m)

for image in openwebrx-rtlsdr openwebrx-sdrplay openwebrx-hackrf openwebrx-airspy openwebrx-full openwebrx; do
  docker push jketterl/$image:$ARCH
done
