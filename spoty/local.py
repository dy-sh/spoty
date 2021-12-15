from spoty import sp
from spoty import log
import spoty.utils
import spoty.like
import os.path
import click
import time


def get_local_tracks(path):
    full_file_names = [os.path.join(dp, f) for dp, dn, filenames in os.walk(path) for f in filenames if
              os.path.splitext(f)[1] == '.flac' or  os.path.splitext(f)[1] == '.mp3']

    return full_file_names