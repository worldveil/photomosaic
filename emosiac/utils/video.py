import subprocess
import os
import math

def extract_audio(src_videopath, dst_audiopath, overwrite=True, verbose=1):
    """
    first grab the audio from the video
    overwrite if neeeded (-y)
    copy the audio (no codec change)
    remove the video (-vn)

    Example:

        $ ffmpeg -y \
            -i images/vids/fireworks.mp4 \
            -vn \
            images/vids/fireworks_audio.mp4
    """
    cmd = "ffmpeg %(ow)s -i %(src)s -vn %(dst)s" % dict(
        src=src_videopath,
        dst=dst_audiopath,
        ow='-y' if overwrite else '',
    )
    if verbose:
        print(cmd)
    process = subprocess.Popen(cmd.split(' '), shell=False, stdout=subprocess.PIPE)
    process.wait()
    if process.returncode != 0:
        return False
    return True

def add_audio_to_video(dst_savepath, src_audiopath, src_videopath, overwrite=True, verbose=1):
    """
    Let's take this audio & our mosiac video as input
    overwrite if neeeded (-y)
    then select streams to add with map:
      -map 0:0 -> take first stream from first (video) file
      -map 1:0 -> take first stream from second (audio) file
    just copy the video, no codec changes
    convert the audio to aac
    we use the shortest of the two streams, cut after 

    Example:

        $ ffmpeg -y \
            -i video-scale-6.avi \
            -i images/vids/fireworks_audio.mp4 \
            -map 0:0 \
            -map 1:0 \
            -c:v copy \
            -shortest \
            video-scale-6-with-audio.mp4
    """
    cmd = """ffmpeg %(overwrite)s \
-i %(src_videopath)s \
-i %(src_audiopath)s \
-map 0:0 \
-map 1:0 \
-c:v copy \
-shortest \
%(dst_savepath)s""" % dict(
        dst_savepath=dst_savepath, 
        src_audiopath=src_audiopath,
        src_videopath=src_videopath,
        overwrite='-y' if overwrite else ''
    )
    if verbose:
        print(cmd)
    process = subprocess.Popen(cmd.split(' '), shell=False, 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    if process.returncode != 0:
        return False
    return True

def probe_length(mediapath, verbose=0):
    cmd = "ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 %(path)s" % dict(
        path=mediapath,
    )
    if verbose:
        print(cmd)
    process = subprocess.Popen(cmd.split(' '), shell=False, 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    out, _ = process.communicate()
    try:
        return float(out.strip())
    except ValueError:
        return None

def probe_fps(mediapath, verbose=0):
    cmd = "ffprobe -v error -select_streams v -of default=noprint_wrappers=1:nokey=1 -show_entries stream=r_frame_rate %(path)s" % dict(
        path=mediapath,
    )
    if verbose:
        print(cmd)
    process = subprocess.Popen(cmd.split(' '), shell=False, 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    out, _ = process.communicate()
    try:
        return float(out.strip())
    except ValueError:
        return None

def calculate_framecount(videopath, verbose=1):
    return int(math.ceil(probe_length(videopath) * probe_fps(videopath)))

def compress_video(src, dst):
    """
    https://gist.github.com/lukehedger/277d136f68b028e22bed
    
    ffmpeg -i input.mp4 -vcodec h264 -acodec aac output.mp4
    """
    pass
