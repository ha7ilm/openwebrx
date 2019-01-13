FROM raspbian/stretch

ADD docker/install-dependencies.sh /
RUN /install-dependencies.sh

ADD . /openwebrx

WORKDIR /openwebrx

CMD python2.7 openwebrx.py 
EXPOSE 8073
