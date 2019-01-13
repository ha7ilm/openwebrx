FROM raspbian/stretch

RUN apt-get update &&\
    apt-get -y install sox libfftw3-dev python rtl-sdr netcat libitpp-dev libsndfile1-dev

ADD docker/install-dependencies.sh /
RUN /install-dependencies.sh

ADD . /openwebrx

WORKDIR /openwebrx

CMD python openwebrx.py 
EXPOSE 8073
