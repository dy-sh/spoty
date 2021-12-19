from spoty import settings
from spoty import log
import spoty.spotify
import spoty.utils
import spoty.csv_playlist
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
    count = spoty.spotify.get_liked_tracks_count()
    click.echo(f'Liked tracks: {count}')


@like.command("add")
@click.argument("track_ids",  nargs=-1)
def like_add(track_ids):
    r"""
    Add tracks to liked tracks.

    TRACK_IDS - list of track IDs or URIs. You can specify one ID or many IDs separated by a space.

    Examples:

        spoty like add  00i9VF7sjSaTqblAuKFBDO

        spoty like add  00i9VF7sjSaTqblAuKFBDO 7cjlfruK9Oqw7k5wAZGO72

        spoty like add https://open.spotify.com/track/00i9VF7sjSaTqblAuKFBDO
    """

    track_ids = list(track_ids)
    spoty.spotify.add_tracks_to_liked(track_ids)
    click.echo(f'{len(track_ids)} tracks added to liked')


@like.command("export")
@click.option('--path',  default=settings.DEFAULT_LIBRARY_PATH, help='Path to create file')
@click.option('--file-name',  default=settings.DEFAULT_LIKES_EXPORT_FILE_NAME, help='File name to create')
@click.option('--dest_csv_overwrite', '-o', type=bool, is_flag=True, default=False,
              help='Overwrite existing files without asking')
@click.option('--dest_csv_timestamp', '-t', type=bool, is_flag=True, default=False,
              help='Create a subfolder with the current date and time (it can be convenient for creating backups)')
def like_export(path, file_name, overwrite, timestamp):
    r"""Export the list of liked tracks to csv file on disk.

    Examples:

        spoty playlist export

        spoty playlist export --file-name "C:\Users\User\Downloads"
    """

    path = os.path.abspath(path)

    if timestamp:
        now = datetime.now()
        date_time_str = now.strftime("%Y_%m_%d-%H_%M_%S")
        path = os.path.join(path, date_time_str)

    file_name = os.path.join(path, file_name)

    if os.path.isfile(file_name) and not overwrite:
        time.sleep(0.2)  # waiting progressbar updating
        if not click.confirm(f'\nFile "{file_name}" already exist. Overwrite?'):
            click.echo("Aborted!")
            log.info(f'Canceled by user (file already exist)')
            return

    liked_tracks =spoty.spotify.export_liked_tracks_to_file(file_name)

    click.echo(f'{len(liked_tracks)} liked tracks exported to file: "{file_name}"')

    return file_name


@like.command("import")
@click.argument('file_names',  nargs=-1)
def like_import(file_names):
    r"""Import liked tracks to yor library from csv file on disk.

    FILE_NAMES - list of file names to import. You can specify one file or many files separated by a space.

    Examples:

        spoty like import "C:\Users\User\Downloads\export\likes.csv"

        spoty like import "C:\Users\User\Downloads\export\likes1.csv" "C:\Users\User\Downloads\export\likes2.csv"
    """

    all_tracks_in_file = []
    with click.progressbar(file_names, label='Importing lied tracks') as bar:
        for file_name in bar:
            try:
                tracks_in_file = spoty.spotify.import_likes_from_file(file_name)
                all_tracks_in_file += tracks_in_file
            except FileNotFoundError:
                time.sleep(0.2)  # waiting progressbar updating
                click.echo(f'\nFile does not exist: "{file_name}"')
            except spoty.csv_playlist.CSVFileEmpty as e:
                time.sleep(0.2)  # waiting progressbar updating
                log.warning(f'Cant import file "{file_name}". File is empty.')
                click.echo(f'\nCant import file "{file_name}". File is empty.')
            except spoty.csv_playlist.CSVFileInvalidHeader as e:
                time.sleep(0.2)  # waiting progressbar updating
                mess = f'Cant import file "{file_name}". The header of csv table does not contain any of the required ' \
                       f'fields (isrc, spotify_track_id, title).'
                log.error(mess)
                click.echo('\n' + mess)

    click.echo(f'{len(all_tracks_in_file)} liked tracks imported')


