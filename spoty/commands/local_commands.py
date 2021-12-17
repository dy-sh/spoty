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


@local.command("count-tracks")
@click.argument('path', type=str)
@click.option('--filter-names', type=str, default=None,
              help='Count only files whose names matches this regex filter')
@click.option('--have-tag', type=str, default=None,
              help='Count only files that have all of the specified tags.')
@click.option('--have-no-tag', type=str, default=None,
              help='Count only files that do not have any of the listed tags.')
@click.option('--recursive', '-r', type=bool, is_flag=True, default=False,
              help='Search in subfolders.')
def local_count_tracks(path, recursive, filter_names, have_tag, have_no_tag):
    r"""
    Displays the number of local tracks found in the folder.

    PATH - Path to search files

    Examples:

        spoty local count-tracks "C:\Users\User\Downloads\music"

        spoty local count-tracks -r "C:\Users\User\Downloads\music"

        spoty local count-tracks -r --have-tags "isrc,genre" "C:\Users\User\Downloads\music"

        spoty local count-tracks --filter-names "^awesome" "C:\Users\User\Downloads\music"
    """
    path = os.path.abspath(path)

    have_tags = have_tag.upper().split(',') if have_tag is not None else []
    have_no_tags = have_no_tag.upper().split(',') if have_no_tag is not None else []
    full_file_names = spoty.local.get_local_tracks_file_names(path, recursive, filter_names, have_tags, have_no_tags)

    click.echo(f'Local tracks: {len(full_file_names)}')


@local.command("list-tracks")
@click.argument('path', type=str)
@click.option('--filter-names', type=str, default=None,
              help='List only files whose names matches this regex filter')
@click.option('--have-tag', type=str, default=None,
              help='List only files that have all of the specified tags.')
@click.option('--have-no-tag', type=str, default=None,
              help='List only files that do not have any of the listed tags.')
@click.option('--recursive', '-r', type=bool, is_flag=True, default=False,
              help='Search in subfolders.')
def local_list_tracks(path, recursive, filter_names, have_tag, have_no_tag):
    r"""
    Displays the list of local tracks found in the folder.

    PATH - Path to search files

    Examples:

        spoty local list-tracks "C:\Users\User\Downloads\music"

        spoty local list-tracks -r "C:\Users\User\Downloads\music"

        spoty local list-tracks -r --have-isrc "C:\Users\User\Downloads\music"

        spoty local list-tracks --filter-names "^awesome" "C:\Users\User\Downloads\music"
    """
    path = os.path.abspath(path)

    have_tags = have_tag.upper().split(',') if have_tag is not None else []
    have_no_tags = have_no_tag.upper().split(',') if have_no_tag is not None else []
    full_file_names = spoty.local.get_local_tracks_file_names(path, recursive, filter_names, have_tags, have_no_tags)

    click.echo(f'Local tracks:')
    for full_file in full_file_names:
        click.echo(full_file)

    click.echo(f'Total tracks: {len(full_file_names)}')


@local.command("collect-playlist")
@click.argument('tracks-path', type=str)
@click.argument('export-path', type=str)
@click.option('--filter-names', type=str, default=None,
              help='Export only playlists whose names matches this regex filter')
@click.option('--overwrite', '-o', type=bool, is_flag=True, default=False,
              help='Overwrite existing files without asking')
@click.option('--timestamp', '-t', type=bool, is_flag=True, default=False,
              help='Create a subfolder with the current date and time (it can be convenient for creating backups)')
@click.option('--have-tag', type=str, default=None,
              help='Collect only files that have all of the specified tags.')
@click.option('--have-no-tag', type=str, default=None,
              help='Collect only files that do not have any of the listed tags.')
@click.option('--naming-pattern', type=str, default=None,
              help='')
def local_collect_playlists(tracks_path, export_path, filter_names, overwrite, timestamp, naming_pattern, have_tag,
                            have_no_tag):
    r"""Create playlists from your local tracks and save to csv files on disk.

    TRACKS_PATH - path where local music files located

    EXPORT_PATH - path where to create playlists files

    If "--naming-pattern" flag is not set, then playlist names will be generated from the name of the subfolder where the files are located.
    if "--naming-pattern" flag is set, then the playlists will be named according to the pattern. Any tags from the tracks can be used in the template.


    Examples:

        spoty local collect-playlist "C:\Users\User\Downloads\music" "C:\Users\User\Downloads\export"

        Export only playlists whose names starts with "awesome":

            spoty local collect-playlist --filter-names "^awesome" "C:\Users\User\Downloads\music" "C:\Users\User\Downloads\export"

        Export playlists by genres:

            spoty local collect-playlist --naming-pattern "%genre%" "C:\Users\User\Downloads\music" "C:\Users\User\Downloads\export"

        Export playlists by genre and mood:

            spoty local collect-playlist --naming-pattern "%genre% - %mood%" "C:\Users\User\Downloads\music" "C:\Users\User\Downloads\export"
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

    have_tags = have_tag.upper().split(',') if have_tag is not None else []
    have_no_tags = have_no_tag.upper().split(',') if have_no_tag is not None else []

    if naming_pattern is None:
        with click.progressbar(directories, label='Exporting playlists') as bar:
            for dir in bar:
                tracks_file_names = spoty.local.get_local_tracks_file_names(dir, False, filter_names, have_tags,
                                                                            have_no_tags)

                if len(tracks_file_names) == 0:
                    continue

                playlist_name = os.path.basename(os.path.normpath(dir))
                playlist_file_name = os.path.join(export_path, playlist_name + '.csv')

                spoty.local.collect_playlist_from_files(playlist_file_name, tracks_file_names, overwrite)

                all_track_file_names.extend(tracks_file_names)
                playlist_names.append(playlist_name)
                playlist_file_names.append(playlist_file_name)
    else:
        with click.progressbar(directories, label='Collecting tracks') as bar:
            for dir in bar:
                tracks_file_names = spoty.local.get_local_tracks_file_names(dir, False, filter_names, have_tags,
                                                                            have_no_tags)

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


@local.command("count-in-playlists")
@click.argument('path', type=str)
@click.option('--filter-names', type=str, default=None,
              help='Read only playlists whose names matches this regex filter')
@click.option('--recursive', '-r', type=bool, is_flag=True, default=False,
              help='Search in subfolders.')
@click.option('--have-tag', type=str, default=None,
              help='Count only tracks that have all of the specified tags.')
@click.option('--have-no-tag', type=str, default=None,
              help='Count only tracks that do not have any of the listed tags.')
def local_count_tracks_in_playlists(path, filter_names, recursive, have_tag, have_no_tag):
    r"""Displays the number of tracks found in local playlists.

    PATH - Path to search files

    Examples:

        spoty local count-in-playlists "C:\Users\User\Downloads\music"

        spoty local count-in-playlists -r "C:\Users\User\Downloads\music"

        spoty local count-in-playlists --filter-names "^awesome" "C:\Users\User\Downloads\music"
    """

    path = os.path.abspath(path)

    all_tracks = []

    playlists = spoty.local.get_all_playlists_in_path(path, recursive, filter_names)
    for file_name in playlists:
        tracks = spoty.local.read_tracks_from_csv_file(file_name)

        for track in tracks:
            if have_tag is not None:
                tags = have_tag.upper().split(',')
                if not spoty.local.check_track_have_all_tags(track, tags):
                    continue

            if have_no_tag is not None:
                tags = have_no_tag.upper().split(',')
                if spoty.local.check_track_have_all_tags(track, tags):
                    continue

            all_tracks.append(track)

    click.echo(f'Found {len(all_tracks)} tracks in {len(playlists)} playlistss')


@local.command("list-duplicates-in-playlists")
@click.argument('path', type=str)
@click.option('--filter-names', type=str, default=None,
              help='Read only playlists whose names matches this regex filter')
@click.option('--recursive', '-r', type=bool, is_flag=True, default=False,
              help='Search in subfolders.')
def local_list_duplicates_in_playlists(path, filter_names, recursive):
    r"""Displays the list of duplicates found in local playlists.

    PATH - Path to search files

    Examples:

        spoty local list-duplicates-in-playlists "C:\Users\User\Downloads\music"

        spoty local list-duplicates-in-playlists -r "C:\Users\User\Downloads\music"

        spoty local list-duplicates-in-playlists --filter-names "^awesome" "C:\Users\User\Downloads\music"
    """

    path = os.path.abspath(path)

    all_tracks = []

    duplicates_dic = spoty.local.find_duplicates_in_playlists_by_isrc(path, recursive, filter_names)



    i = 0
    for isrc, duplicates in duplicates_dic.items():
        i += 1
        click.echo(f"======================= DUPLICATE {i}/{len(duplicates_dic)} =============================")
        click.echo(f'{len(duplicates)} duplicates with ISRC: {isrc}')
        click.echo("-----------------------------------------------------")
        for track in duplicates:
            click.echo(f'Track {track["playlist_index"]} in playlist "{track["playlist_name"]}"')
            spoty.local.print_track_main_tags(track)


    click.echo(f'Total duplicates found: {len(duplicates_dic)}')