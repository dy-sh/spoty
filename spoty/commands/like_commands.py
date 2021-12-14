import spoty.playlist
import click
import re
from spoty.utils import *
from spoty.core import settings
import time
from datetime import datetime

@click.group()
def like():
    r"""Likes management (favorites)."""
    pass