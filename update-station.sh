#!/usr/bin/env bash

URL="HTTP_URL_TO_FILE"
STATIONS_FILE="stations.yaml"

rm $STATIONS_FILE
wget --no-check-certificate --no-cache --no-cookies $URL -O $STATIONS_FILE
cat $STATIONS_FILE
