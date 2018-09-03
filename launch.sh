export CONTAINER_NAME=emoji_test

docker run  \
	--rm \
	--name $CONTAINER_NAME \
	--mount type=bind,source="$(pwd)",target=/project \
	-p 8888:8888/tcp \
	emoji-conda:latest \
	jupyter notebook \
		--allow-root \
		--ip 0.0.0.0 \
		--no-browser \
		--NotebookApp.token='' \
		--notebook-dir=/project
