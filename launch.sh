export CONTAINER_NAME=mosaic_container
export IP=`ifconfig en0 | grep inet | awk '$1=="inet" {print $2}'`
export PORT=8888

# ensure we can talk to the host machine's IP
xhost + $IP

# start a Docker container which will die on exit
# this will run an IPython server which you can access in
# your browser at localhost:$PORT
docker run \
	--rm \
	--name $CONTAINER_NAME \
	--mount type=bind,source="$(pwd)",target=/project \
	-p "$PORT:$PORT/tcp" \
	-e "DISPLAY=$IP:0" \
	mosaic-conda:latest \
	jupyter notebook \
		--allow-root \
		--ip 0.0.0.0 \
		--no-browser \
		--NotebookApp.token='' \
		--notebook-dir=/project
