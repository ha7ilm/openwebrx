#!/bin/bash
set -euxo pipefail

apt-get update
apt-get -y install --no-install-recommends rtl-sdr

apt-get autoremove --purge -y
rm -rf /var/lib/apt/lists/*

