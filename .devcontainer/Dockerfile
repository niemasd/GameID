# Minimal Docker image for GameID using Ubuntu base
FROM ubuntu:20.04
MAINTAINER Niema Moshiri <niemamoshiri@gmail.com>

# Set up environment and install dependencies
RUN apt-get update && apt-get -y upgrade && \
    apt-get install -y git python3 python3-pip wget && \
    pip3 install --no-cache-dir pycdlib && \

    # clean up
    rm -rf /root/.cache /tmp/*
