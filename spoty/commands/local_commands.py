from spoty import log
import spoty.spotify_api
import spoty.csv_playlist
import spoty.utils
import spoty.audio_files
import spoty.audio_files
import click
import os
import time
from datetime import datetime
import re


@click.group()
def local():
    r"""Local audio files management."""
    pass

