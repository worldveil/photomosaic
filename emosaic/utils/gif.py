import os
import moviepy.editor as mpy

def create_gif_from_images(image_paths, savepath, fps=3, fuzz=5, ascending=None, compress=True, resize_height=None):
    if ascending is True:
        image_paths.sort(reverse=False)
    elif ascending is False:
        image_paths.sort()

    tmp_path = os.path.join('/tmp', os.path.basename(savepath))
    clip = mpy.ImageSequenceClip(image_paths, fps=fps)
    clip.write_gif(tmp_path, fps=fps, fuzz=fuzz)

    # now compress
    if compress:
        try:
            os.system("du -h %s" % tmp_path)
            print("Attempting to compress file at: %s" % tmp_path)
            if resize_height:
                cmd = "gifsicle -O3 --resize-height %d < %s > %s" % (resize_height, tmp_path, savepath)
            else:
                cmd = "gifsicle -O3 < %s > %s" % (tmp_path, savepath)
            os.system(cmd)
        except Exception:
            os.system("cp %s %s" % (tmp_path, savepath))
    else:
        os.system("cp %s %s" % (tmp_path, savepath))

    os.remove(tmp_path)
