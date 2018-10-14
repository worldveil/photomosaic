import moviepy.editor as mpy

def create_gif_from_images(image_paths, savepath, fps=3, fuzz=5, ascending=False):
    if ascending:
        image_paths.sort(reverse=True)
    else:
        image_paths.sort()

    clip = mpy.ImageSequenceClip(image_paths, fps=fps)
    clip.write_gif(savepath, fps=fps, fuzz=fuzz)
