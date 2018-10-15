import os

def ensure_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def is_running_jupyter():
    try:
        return type(get_ipython()).__module__.startswith('ipykernel.')
    except NameError:
        return False
