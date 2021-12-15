from spoty import settings
from spoty import log
import spoty.like
import spoty.utils
import spoty.local
import click
import os
import time
from datetime import datetime
import re


@click.group()
def local():
    r"""Local files management."""
    pass


@local.command("count")
@click.argument('path', type=str)
@click.option('--filter-names', type=str, default=None,
              help='Count only files whose names matches this regex filter')
def local_count(path, filter_names):
    r"""
    Displays the number of local tracks.

    Examples:

        spoty local count "C:\Users\User\Downloads\music"

        spoty local count --filter-names "^awesome" "C:\Users\User\Downloads\music"
    """
    full_file_names = spoty.local.get_local_tracks(path)

    file_names = [os.path.basename(filenames) for filenames in full_file_names]

    if filter_names is not None:
        file_names = list(filter(lambda file: re.findall(filter_names, file), file_names))

    click.echo(f'Local tracks: {len(file_names)}')


@local.command("list")
@click.argument('path', type=str)
@click.option('--filter-names', type=str, default=None,
              help='List only files whose names matches this regex filter')
@click.option('--have-isrc', '-d', type=bool, is_flag=True, default=False,
              help='List only files that have ISRC tag.')
def local_list(path, filter_names):
    r"""
    Displays the number of local tracks.

    Examples:

        spoty local list "C:\Users\User\Downloads\music"

        spoty local list --filter-names "^awesome" "C:\Users\User\Downloads\music"
    """
    full_file_names = spoty.local.get_local_tracks(path)

    if filter_names is not None:
        full_file_names = list(filter(lambda full_file_name:
                                      re.findall(filter_names, os.path.basename(full_file_name)),
                                      full_file_names))

    click.echo(f'Local tracks:')
    for full_file in full_file_names:
        click.echo(full_file)

    click.echo(f'Total tracks: {len(full_file_names)}')
