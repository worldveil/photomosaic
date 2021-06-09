param($PicturesDir="c:\Users\$env:UserName\Pictures", $ProjectDir="$pwd", $ContainerName="Photomosaic")

$env:HostIP = (
    Get-NetIPConfiguration |
    Where-Object {
        $_.IPv4DefaultGateway -ne $null -and
        $_.NetAdapter.Status -ne "Disconnected"
    }
).IPv4Address.IPAddress

docker run --rm --name $ContainerName `
	--mount type=bind,source="$ProjectDir",target="/project" `
	--mount type=bind,source="$PicturesDir",target="/pics" `
	-p "8888:8888/tcp" -e "DISPLAY=$env:HostIP:0" `
	mosaic-conda:latest `
	jupyter notebook `
		--allow-root `
		--ip 0.0.0.0 `
		--no-browser `
		--NotebookApp.token='' `
		--notebook-dir=/project
