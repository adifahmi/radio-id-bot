#!/usr/bin/env bash

URL="HTTP_URL"
STATIONS_FILE="stations.yaml"
RANDOM_STRING=`openssl rand -hex 5`
URL_NO_CACHE="${URL}?cachebust=${RANDOM_STRING}"

rm $STATIONS_FILE
wget --no-check-certificate --no-cache --no-cookies $URL_NO_CACHE -O $STATIONS_FILE
cat $STATIONS_FILE
