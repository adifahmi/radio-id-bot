#!/usr/bin/env bash

URL="HTTP_URL_TO_FILE"
STATIONS_FILE="stations.yaml"

rm $STATIONS_FILE
wget $URL -O $STATIONS_FILE
cat $STATIONS_FILE
