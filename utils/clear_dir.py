import os

def clear_dir(dir_path):
    """Deletes all files in the given directory.

    Args:
        dir_path: The path to the directory.
    """
    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)