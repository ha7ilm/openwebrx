#!/bin/bash
docker build -t openwebrx-base -f docker/Dockerfiles/Dockerfile-base .
docker build -t jketterl/openwebrx-rtlsdr -t jketterl/openwebrx -f docker/Dockerfiles/Dockerfile-rtlsdr .
docker build -t jketterl/openwebrs-sdrplay -f docker/Dockerfiles/Dockerfile-sdrplay .
