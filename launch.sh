export CONTAINER_NAME=emoji_test

docker run  \
	--rm \
	--name $CONTAINER_NAME \
	--mount type=bind,source="$(pwd)",target=/project \
	-p 8888:8888/tcp \
	emoji:latest \
	jupyter notebook \
		--allow-root \
		--ip 0.0.0.0 \
		--no-browser \
		--NotebookApp.token='' \
		--notebook-dir=/project

# docker run \
# 	--rm \
# 	--name genres_test \
# 	--mount type=bind,source="$(pwd)"/music,target=/project/music \
# 	--mount type=bind,source="$(pwd)"/computed,target=/project/computed \
# 	--mount type=bind,source="$(pwd)"/data,target=/project/data \
# 	--mount type=bind,source="$(pwd)"/checkpoints,target=/project/checkpoints \
# 	-p 8888:8888/tcp \
# 	-p 6006:6006/tcp \
# 	genres:latest jupyter notebook --allow-root