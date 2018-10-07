export CONTAINER_NAME=emoji_test
export IP=`ifconfig en0 | grep inet | awk '$1=="inet" {print $2}'`

xhost + $IP

docker run  \
	--rm \
	--name $CONTAINER_NAME \
	--mount type=bind,source="$(pwd)",target=/project \
	-p 8888:8888/tcp \
	-e "DISPLAY=$IP:0" \
	emoji-conda:latest \
	jupyter notebook \
		--allow-root \
		--ip 0.0.0.0 \
		--no-browser \
		--NotebookApp.token='' \
		--notebook-dir=/project
