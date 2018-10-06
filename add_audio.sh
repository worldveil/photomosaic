# first grab the audio from the video
# overwrite if neeeded (-y)
# copy the audio (no codec change)
# remove the video (-vn)
ffmpeg -y -i images/vids/fireworks.mp4 \
	-vn \
	images/vids/fireworks_audio.mp4

# then, mosaicify
python video.py \
	--codebook-dir images/pics/ \
	--target "images/vids/fireworks.mp4" \
	--scale 12 \
	--height-aspect 4 \
	--width-aspect 3 

# next, let's take this audio & our mosiac video as input
# then map (?)
# just copy the video, no codec changes
# convert the audio to aac
# we use the shortest of the two streams, cut after 
ffmpeg \
	-i video-scale-6.avi \
	-i images/vids/fireworks_audio.mp4 \
	-map 0:0 -map 1:0 \
	-c:v copy \
	-shortest \
	video-scale-6-with-audio.mp4
