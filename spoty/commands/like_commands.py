from spoty import settings
from spoty import log
import spoty.like
import spoty.utils
import click
import os
import time
from datetime import datetime

@click.group()
def like():
    r"""Likes management (favorites)."""
    pass


@like.command("count")
def like_count():
    r"""
    Displays the number of liked tracks.

    Examples:

        spoty like count
    """
    count = spoty.like.get_liked_tracks_count()
    click.echo(f'Liked tracks: {count}')


@like.command("add")
@click.argument("track_ids", type=str, nargs=-1)
def like_add(track_ids):
    r"""
    Add tracks to liked tracks.

    TRACK_IDS - list of track IDs or URIs. You can specify one ID or many IDs separated by a space.

    Examples:

        spoty like add  00i9VF7sjSaTqblAuKFBDO

        spoty like add  00i9VF7sjSaTqblAuKFBDO 7cjlfruK9Oqw7k5wAZGO72

        spoty like add https://open.spotify.com/track/00i9VF7sjSaTqblAuKFBDO
    """

    spoty.like.add_tracks(track_ids)
    click.echo(f'{len(track_ids)} tracks added to liked')


@like.command("export-all")
@click.option('--path', type=str, default=settings.DEFAULT_LIBRARY_PATH, help='Path to create file')
@click.option('--file-name', type=str, default=settings.DEFAULT_LIKES_EXPORT_FILE_NAME, help='File name to create')
@click.option('--overwrite', '-o', type=bool, is_flag=True, default=False,
              help='Overwrite existing files without asking')
@click.option('--timestamp', '-t', type=bool, is_flag=True, default=False,
              help='Create a subfolder with the current date and time (it can be convenient for creating backups')
def like_export_all(path, file_name, overwrite, timestamp):
    r"""Export the list of liked tracks to csv file on disk.

    Examples:

        spoty playlist export-all

        spoty playlist export-all --file-name "C:\Users\User\Downloads"
    """

    path = os.path.abspath(path)

    if timestamp:
        now = datetime.now()
        date_time_str = now.strftime("%Y_%m_%d-%H_%M_%S")
        path = os.path.join(path, date_time_str)

    file_name = os.path.join(path, file_name)

    liked_tracks = spoty.like.get_liked_tracks()

    if os.path.isfile(file_name) and not overwrite:
        time.sleep(0.2)  # waiting progressbar updating
        if not click.confirm(f'\nFile "{file_name}" already exist. Overwrite?'):
            log.info(f'Canceled by user (file already exist)')
            return

    spoty.utils.write_tracks_to_csv_file(liked_tracks, file_name)

    log.success(f'Liked tracks exported to file: "{file_name}")')
    click.echo(f'Liked tracks exported to file: "{file_name}")')

    return file_name
