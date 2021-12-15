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
@click.option('--have-isrc', type=bool, is_flag=True, default=False,
              help='Count only files that have ISRC tag.')
@click.option('--have-no-isrc', type=bool, is_flag=True, default=False,
              help='Count only files that have no ISRC tag.')
@click.option('--recursive', '-r', type=bool, is_flag=True, default=False,
              help='Search in subfolders.')
def local_count(path, recursive, filter_names, have_isrc, have_no_isrc):
    r"""
    Displays the number of local tracks.

    Examples:

        spoty local count "C:\Users\User\Downloads\music"

        spoty local list -r "C:\Users\User\Downloads\music"

        spoty local list -r --have-isrc "C:\Users\User\Downloads\music"

        spoty local count --filter-names "^awesome" "C:\Users\User\Downloads\music"
    """
    full_file_names = spoty.local.get_local_tracks_file_names(path, recursive, filter_names, have_isrc, have_no_isrc)

    click.echo(f'Local tracks: {len(full_file_names)}')


@local.command("list")
@click.argument('path', type=str)
@click.option('--filter-names', type=str, default=None,
              help='List only files whose names matches this regex filter')
@click.option('--have-isrc', type=bool, is_flag=True, default=False,
              help='List only files that have ISRC tag.')
@click.option('--have-no-isrc', type=bool, is_flag=True, default=False,
              help='List only files that have no ISRC tag.')
@click.option('--recursive', '-r', type=bool, is_flag=True, default=False,
              help='Search in subfolders.')
def local_list(path, recursive, filter_names, have_isrc, have_no_isrc):
    r"""
    Displays the number of local tracks.

    Examples:

        spoty local list "C:\Users\User\Downloads\music"

        spoty local list -r "C:\Users\User\Downloads\music"

        spoty local list -r --have-isrc "C:\Users\User\Downloads\music"

        spoty local list --filter-names "^awesome" "C:\Users\User\Downloads\music"
    """
    full_file_names = spoty.local.get_local_tracks_file_names(path, recursive, filter_names, have_isrc, have_no_isrc)

    click.echo(f'Local tracks:')
    for full_file in full_file_names:
        click.echo(full_file)

    click.echo(f'Total tracks: {len(full_file_names)}')


@local.command("export-all")
@click.argument('tracks-path', type=str)
@click.argument('export-path', type=str)
@click.option('--filter-names', type=str, default=None,
              help='Export only playlists whose names matches this regex filter')
@click.option('--overwrite', '-o', type=bool, is_flag=True, default=False,
              help='Overwrite existing files without asking')
@click.option('--confirm', '-c', type=bool, is_flag=True, default=False,
              help='Do not ask for export confirmation')
@click.option('--timestamp', '-t', type=bool, is_flag=True, default=False,
              help='Create a subfolder with the current date and time (it can be convenient for creating backups)')
@click.option('--naming-pattern', type=str, default=None,
              help='')
def local_export_all(tracks_path, export_path, filter_names, overwrite, confirm, timestamp, naming_pattern):
    r"""Export all playlists from your local library to csv files on disk.

    TRACKS_PATH - path where local music files located

    EXPORT_PATH - path where to create playlists files

    If "--naming-pattern" flag is not set, then playlist names will be generated from the name of the subfolder where the files are located.
    if "--naming-pattern" flag is set, then the playlists will be named according to the pattern. Any tags from the tracks can be used in the template.


    Examples:

        spoty local export-all "C:\Users\User\Downloads\music" "C:\Users\User\Downloads\export"

        Export only playlists whose names starts with "awesome":

            spoty local export-all --filter-names "^awesome" "C:\Users\User\Downloads\music" "C:\Users\User\Downloads\export"

        Export playlists by genres:

            spoty local export-all --naming-pattern "%genre%" "C:\Users\User\Downloads\music" "C:\Users\User\Downloads\export"

        Export playlists by genre and mood:

            spoty local export-all --naming-pattern "%genre% - %mood%" "C:\Users\User\Downloads\music" "C:\Users\User\Downloads\export"
    """

    path = os.path.abspath(tracks_path)

    directories = []
    for (dirpath, dirnames, filenames) in os.walk(path):
        directories.append(dirpath)

    all_track_file_names = []
    all_track_tags = []
    playlist_names = []
    playlist_file_names = []

    if timestamp:
        now = datetime.now()
        date_time_str = now.strftime("%Y_%m_%d-%H_%M_%S")
        export_path = os.path.join(export_path, date_time_str)

    if naming_pattern is None:
        with click.progressbar(directories, label='Exporting playlists') as bar:
            for dir in bar:
                tracks_file_names = spoty.local.get_local_tracks_file_names(dir, False, filter_names)

                if len(tracks_file_names) == 0:
                    continue

                playlist_name = os.path.basename(os.path.normpath(dir))
                playlist_file_name = os.path.join(export_path, playlist_name + '.csv')

                spoty.local.export_playlist_to_file(playlist_file_name, tracks_file_names, overwrite)

                all_track_file_names.extend(tracks_file_names)
                playlist_names.append(playlist_name)
                playlist_file_names.append(playlist_file_name)
    else:
        with click.progressbar(directories, label='Collecting tracks') as bar:
            for dir in bar:
                tracks_file_names = spoty.local.get_local_tracks_file_names(dir, False, filter_names)

                if len(tracks_file_names) == 0:
                    continue

                all_track_file_names.extend(tracks_file_names)
                tags = spoty.local.read_tracks_tags(tracks_file_names)
                all_track_tags.extend(tags)

        grouped_tracks = spoty.local.group_tracks_by_pattern(naming_pattern, all_track_tags)
        for key, value in grouped_tracks.items():
            playlist_name = key
            playlist_name = spoty.utils.slugify_file_pah(playlist_name)
            playlist_file_name = os.path.join(export_path, playlist_name + '.csv')

            if os.path.isfile(playlist_file_name) and not overwrite:
                time.sleep(0.2)  # waiting progressbar updating
                if not click.confirm(f'\nFile "{playlist_file_name}" already exist. Overwrite?'):
                    continue

            spoty.local.write_tracks_to_csv_file(value, playlist_file_name)

            playlist_names.append(playlist_name)
            playlist_file_names.append(playlist_file_name)


    mess = f'{len(all_track_file_names)} tracks exported to {len(playlist_names)} playlists in path: "{export_path}"'
    log.success(mess)
    click.echo(mess)
