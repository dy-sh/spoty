from spoty import settings
from spoty import log
import spoty.spotify_api
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

        spoty spotify like count
    """
    count = spoty.spotify_api.get_liked_tracks_count()
    click.echo(f'Liked tracks: {count}')


@like.command("add")
@click.argument("track_ids", nargs=-1)
def like_add(track_ids):
    r"""
    Add tracks to liked tracks.

    TRACK_IDS - list of track IDs or URIs. You can specify one ID or many IDs separated by a space.

    Examples:

        spoty spotify like add  00i9VF7sjSaTqblAuKFBDO

        spoty spotify like add  00i9VF7sjSaTqblAuKFBDO 7cjlfruK9Oqw7k5wAZGO72

        spoty spotify like add https://open.spotify.com/track/00i9VF7sjSaTqblAuKFBDO
    """

    track_ids = list(track_ids)
    spoty.spotify_api.add_tracks_to_liked(track_ids)
    click.echo(f'{len(track_ids)} tracks added to liked')


@like.command("export")
@click.option('--path', '--p', default=settings.SPOTY.DEFAULT_EXPORT_PATH, help='Path to create file')
@click.option('--file-name', '--f', default=settings.SPOTY.DEFAULT_LIKES_EXPORT_FILE_NAME, help='File name to create')
@click.option('--overwrite', '-o', is_flag=True,
              help='Overwrite existing files without asking')
@click.option('--no-timestamp', '-T', is_flag=True,
              help='Do not create a subfolder with the current date and time')
def like_export(path, file_name, overwrite, no_timestamp):
    r"""Export the list of liked tracks to csv file on disk.

    Examples:

        spoty playlist export

        spoty playlist export --file-name "C:\Users\User\Downloads"
    """

    path = os.path.abspath(path)

    if not no_timestamp:
        now = datetime.now()
        date_time_str = now.strftime("%Y_%m_%d-%H_%M_%S")
        path = os.path.join(path, "export-likes-" + date_time_str)

    file_name = os.path.join(path, file_name)

    if os.path.isfile(file_name) and not overwrite:
        if not click.confirm(f'\nFile "{file_name}" already exist. Overwrite?'):
            click.echo("Aborted!")
            log.info(f'Canceled by user (file already exist)')
            return

    liked_tracks = spoty.spotify_api.export_liked_tracks_to_file(file_name)

    click.echo(f'{len(liked_tracks)} liked tracks exported to file: "{file_name}"')

    return file_name


@like.command("import")
@click.argument('file_names', nargs=-1)
@click.option('unlike', '-u', is_flag=True,
              help='Remove imported tracks from liked tracks (invert).')
def like_import(file_names, unlike):
    r"""Import liked tracks to yor library from csv file on disk.

    FILE_NAMES - list of file names to import. You can specify one file or many files separated by a space.

    Examples:

        spoty spotify like import "C:\Users\User\Downloads\export\likes.csv"

        spoty spotify like import "C:\Users\User\Downloads\export\likes1.csv" "C:\Users\User\Downloads\export\likes2.csv"
    """

    if len(file_names) == 0:
        click.echo("Please, specify file names to import.")
        exit()

    all_tracks_in_file = []

    if len(file_names) > 1:
        with click.progressbar(file_names, label='Importing liked tracks') as bar:
            for file_name in bar:
                try:
                    tracks_in_file = spoty.spotify_api.import_likes_from_file(file_name, unlike, False)
                    all_tracks_in_file += tracks_in_file
                except FileNotFoundError:
                    click.echo(f'\nFile does not exist: "{file_name}"')
                except spoty.csv_playlist.CSVFileEmpty as e:
                    log.warning(f'Cant import file "{file_name}". File is empty.')
                    click.echo(f'\nCant import file "{file_name}". File is empty.')
                except spoty.csv_playlist.CSVFileInvalidHeader as e:
                    mess = f'Cant import file "{file_name}". The header of csv table does not contain any of the required ' \
                           f'fields (isrc, spotify_track_id, title).'
                    log.error(mess)
                    click.echo('\n' + mess)
    else:
        for file_name in file_names:
            try:
                tracks_in_file = spoty.spotify_api.import_likes_from_file(file_name, unlike, True)
                all_tracks_in_file += tracks_in_file
            except FileNotFoundError:
                click.echo(f'\nFile does not exist: "{file_name}"')
            except spoty.csv_playlist.CSVFileEmpty as e:
                log.warning(f'Cant import file "{file_name}". File is empty.')
                click.echo(f'\nCant import file "{file_name}". File is empty.')
            except spoty.csv_playlist.CSVFileInvalidHeader as e:
                mess = f'Cant import file "{file_name}". The header of csv table does not contain any of the required ' \
                       f'fields (isrc, spotify_track_id, title).'
                log.error(mess)
                click.echo('\n' + mess)

    click.echo(f'{len(all_tracks_in_file)} liked tracks imported')
