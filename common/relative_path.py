import os
import pathlib


def get_relative_path(this, path):
    return os.path.normpath(os.path.abspath(os.path.join(
        pathlib.Path(this).parent.absolute(), path)
    ))
