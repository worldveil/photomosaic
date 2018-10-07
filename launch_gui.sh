export CONTAINER_NAME=emoji_test

docker run -it \
	--rm \
	--name $CONTAINER_NAME \
	--mount type=bind,source="$(pwd)",target=/project \
	emoji-conda:latest \
	/bin/bash

# start XQuartz
# turn on remote setting as seen here: https://blogs.oracle.com/oraclewebcentersuite/running-gui-applications-on-native-docker-containers-for-mac
# QUIT AND START XQUARTZ AGAIN
# xhost + `ifconfig en0 | grep inet | awk '$1=="inet" {print $2}'`
# docker run -it --rm --mount type=bind,source="$(pwd)",target=/project emoji-conda:latest /bin/bash
# export DISPLAY=<IP FROM ABOVE>:0
# python interactive.py