from spoty import sp
from spoty import log
import spoty.utils
import spoty.like
import os.path
import click
import time
import re
import music_tag

def get_local_tracks(path,
                     filter_names=None,
                     filter_have_isrc=False,
                     filter_have_no_isrc=False,
                     ):
    full_file_names = [os.path.join(dp, f) for dp, dn, filenames in os.walk(path) for f in filenames if
              os.path.splitext(f)[1] == '.flac' or  os.path.splitext(f)[1] == '.mp3']

    if filter_names is not None:
        full_file_names = list(filter(lambda full_file_name:
                                      re.findall(filter_names, os.path.basename(full_file_name)),
                                      full_file_names))
    if filter_have_isrc:
        filtered = []
        for file_name in full_file_names:
            f = music_tag.load_file(file_name)
            isrc = f['isrc']
            if len(isrc) > 0:
                filtered.append(file_name)
        full_file_names = filtered

    if filter_have_no_isrc:
        filtered = []
        for file_name in full_file_names:
            f = music_tag.load_file(file_name)
            isrc = f['isrc']
            if len(isrc) == 0:
                filtered.append(file_name)
        full_file_names = filtered

    return full_file_names

