#!/usr/bin/env bash

# read .env file
export $(egrep -v '^#' .env | xargs)

URL=$YOUR_GIST_URL
STATIONS_FILE="stations.yaml"
RANDOM_STRING=`openssl rand -hex 5`
URL_NO_CACHE="${URL}?cachebust=${RANDOM_STRING}"

mv $STATIONS_FILE "{$STATIONS_FILE}_temp"
if wget --no-check-certificate --no-cache --no-cookies $URL_NO_CACHE -O $STATIONS_FILE; then
    echo "Success getting new file"
    rm "{$STATIONS_FILE}_temp"
    echo "old file deleted"
else
    echo "WGET failed, revert action"
    mv "{$STATIONS_FILE}_temp" $STATIONS_FILE
fi

echo "Done"
