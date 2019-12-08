#!/usr/bin/env bash
set -euo pipefail

SIGN_KEY_ID=EC56CED77C05107E4C416EF8173873AE062F3A10
SIGN_KEY=$(gpg --armor --export-secret-key $SIGN_KEY_ID)

docker build --pull -t openwebrx-debian-builder:latest -f docker/Dockerfiles/Dockerfile-debian-builder .
docker run -it --name openwebrx-debian-builder -e SIGN_KEY="$SIGN_KEY" -e SIGN_KEY_ID="$SIGN_KEY_ID" openwebrx-debian-builder:latest
mkdir -p packages/buster
docker cp openwebrx-debian-builder:/packages.tar.gz .
tar xvfz packages.tar.gz -C packages/buster
rm packages.tar.gz
docker rm openwebrx-debian-builder
