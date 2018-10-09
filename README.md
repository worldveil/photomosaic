# photo-emoji-mosiac

Creating photomosiac images. 

## Setup

Ensure you have installed:

* `Docker`
* `XQuartz` (version 2.7.5 or higher) if you'd like to run the `interactive.py` OpenCV GUI explorer. Otherwise you don't need it.

I've only tested this on my Mac OS X, but since it's Dockerized it should run anywhere Docker does!

Next, build the Docker images and run a container:

```bash
# build the Docker image (may take a while!)
sh build.sh

# launch an Docker container running an iPython notebook server
sh launch.sh

# then go to http://localhost:8888/
# there you'll be able to run scripts and view GUI 
```

If you'd like to SSH into the Docker container itself, after running the above:

```bash
sh enter.sh
```

## Photomosiac Scripts

### 1) Creating mosaics from an image

Reconstruct an image using a set of other images, downsized and used as tiles. 

```bash
$ python mosaic.py \
    --target "images/pics/2018-04-01 12.00.27.jpg" \
    --savepath "images/output/%s-%d.jpg" \
    --codebook-dir images/pics/ \
    --scale 1 \
    --height-aspect 4 \
    --width-aspect 3 \
    --vectorization-factor 1
```

Arguments:

* `--target`: the image we're trying to reconstruct from other tile images
* `--codebook-dir`: the images we'll create tiles out of (codebook)
* `--scale`: how large/small to make the tiles. Multipler on the aspect ratio.
* `--height-aspect`: height aspect
* `--width-aspect`: width aspect
* `--vectorization-factor`: if we downsize the feature vector before querying (generally don't need to adjust this)


### 2) Creating mosaic videos

Do the same, but with every frame of a video!

```bash
$ python video.py \
    --target "images/vids/fireworks.mp4" \
    --codebook-dir images/pics/ \
    --scale 14 \
    --height-aspect 4 \
    --width-aspect 3 \
    --savepath "images/vids/fireworks-%d.mp4"
```

Arguments:

* `--target`: the video we're trying to reconstruct from other tile images
* `--codebook-dir`: the images we'll create tiles out of (codebook)
* `--scale`: how large/small to make the tiles. Multipler on the aspect ratio.
* `--height-aspect`: height aspect
* `--width-aspect`: width aspect
* `--savepath`: save our video as output to here (only tested on .mp4 extensions)

`ffmpeg` is used for the audio splicing, since OpenCV can't really handle that. 

You can adjust aspect ratio here too, but those and more are optional arguments.  


### 3) Exploring mosaic scales

On a single frame, play around with different scales (sizes) and see which one looks best. 

```bash
$ python interactive.py \
    --target "images/pics/2018-04-01 12.00.27.jpg" \
    --savepath "images/output/%s-%d.jpg" \
    --codebook-dir images/pics/ \
    --min-scale 1 \
    --max-scale 12
```

Arguments:

* `--target`: the image we're trying to reconstruct from other tile images
* `--codebook-dir`: the images we'll create tiles out of (codebook)
* `--min-scale`: start at this scale value (int)
* `--max-scale`: let user increase scale up to this value (int)

You can adjust aspect ratio here too, but those and more are optional arguments. 

### 4) Create a GIF from a series of mosaics at varying tile scales

```bash
$ python make_gif.py \
    --target "images/pics/2018-04-01 12.00.27.jpg" \
    --savepath "images/output/%s-from-%d-to-%d.gif" \
    --codebook-dir images/pics/ \
    --min-scale 5 \
    --max-scale 25 \
    --fps 3
```

### Emojis

This project first started as a way to make photomosaics from emojis. That didn't turn out to be that aesthetically pleasing, but here's a few notes on it.

#### Downloading Emojis

Run the scraping script. Make sure you have `bs4` and `requests` Python packages installed. 

```bash
$ python scripts/scrape_popular_emojis.py
```

To get the set of all (not just popular) emojis, download the 128 x 128 set from [here](https://emojipedia.org/emojione/3.1/).

### Unit tests

There is a small (but embarassingly incomplete) test suite that you can run with:

```bash
sh test.sh
```

Not much coverage at the moment. 
