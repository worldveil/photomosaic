docker run --rm --name Photomosaic --mount type=bind, source="C:\Users\ixb20175\Desktop\Projects\Docker\photomosaic", target="/project" --mount type=bind, source="C:\Users\ixb20175\Pictures", target="/pics" -p "8888:8888/tcp" -e "DISPLAY=