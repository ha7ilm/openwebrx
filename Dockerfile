FROM raspbian/stretch

ADD docker/install-dependencies.sh /
RUN /install-dependencies.sh

ADD . /openwebrx

WORKDIR /openwebrx

VOLUME /config

ENTRYPOINT [ "/openwebrx/docker/run.sh" ]
EXPOSE 8073
