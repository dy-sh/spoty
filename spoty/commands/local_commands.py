from spoty import settings
from spoty import log
import spoty.like
import spoty.utils
import spoty.local
import spoty.playlist
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
@click.argument('path')
@click.option('--filter-names', default=None,
              help='Count only files whose names matches this regex filter')
@click.option('--have-tags', default=None,
              help='Count only files that have all of the specified tags.')
@click.option('--have-no-tags', default=None,
              help='Count only files that do not have any of the listed tags.')
@click.option('--recursive', '-r', type=bool, is_flag=True, default=False,
              help='Search in subfolders.')
def local_count_tracks(path, recursive, filter_names, have_tags, have_no_tags):
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

    have_tags_arr = have_tags.upper().split(',') if have_tags is not None else []
    have_no_tags_arr = have_no_tags.upper().split(',') if have_no_tags is not None else []
    full_file_names = spoty.local.get_local_tracks_file_names(path, recursive, filter_names, have_tags_arr,
                                                              have_no_tags_arr)

    click.echo(f'Local tracks: {len(full_file_names)}')


@local.command("list-tracks")
@click.argument('path')
@click.option('--filter-names', default=None,
              help='List only files whose names matches this regex filter')
@click.option('--have-tags', default=None,
              help='List only files that have all of the specified tags.')
@click.option('--have-no-tags', default=None,
              help='List only files that do not have any of the listed tags.')
@click.option('--recursive', '-r', type=bool, is_flag=True, default=False,
              help='Search in subfolders.')
def local_list_tracks(path, recursive, filter_names, have_tags, have_no_tags):
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

    have_tags_arr = have_tags.upper().split(',') if have_tags is not None else []
    have_no_tags_arr = have_no_tags.upper().split(',') if have_no_tags is not None else []
    full_file_names = spoty.local.get_local_tracks_file_names(path, recursive, filter_names, have_tags_arr,
                                                              have_no_tags_arr)

    click.echo(f'Local tracks:')
    for full_file in full_file_names:
        click.echo(full_file)

    click.echo(f'Total tracks: {len(full_file_names)}')


@local.command("collect-playlist")
@click.argument('tracks-path')
@click.argument('export-path')
@click.option('--filter-names', default=None,
              help='Export only playlists whose names matches this regex filter')
@click.option('--overwrite', '-o', type=bool, is_flag=True, default=False,
              help='Overwrite existing files without asking')
@click.option('--timestamp', '-t', type=bool, is_flag=True, default=False,
              help='Create a subfolder with the current date and time (it can be convenient for creating backups)')
@click.option('--have-tags', default=None,
              help='Collect only files that have all of the specified tags.')
@click.option('--have-no-tags', default=None,
              help='Collect only files that do not have any of the listed tags.')
@click.option('--naming-pattern', default=None,
              help='')
def local_collect_playlists(tracks_path, export_path, filter_names, overwrite, timestamp, naming_pattern, have_tags,
                            have_no_tags):
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

    have_tags_arr = have_tags.upper().split(',') if have_tags is not None else []
    have_no_tags_arr = have_no_tags.upper().split(',') if have_no_tags is not None else []

    if naming_pattern is None:
        with click.progressbar(directories, label='Exporting playlists') as bar:
            for dir in bar:
                tracks_file_names = spoty.local.get_local_tracks_file_names(dir, False, filter_names, have_tags_arr,
                                                                            have_no_tags_arr)

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
                tracks_file_names = spoty.local.get_local_tracks_file_names(dir, False, filter_names, have_tags_arr,
                                                                            have_no_tags_arr)

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
@click.argument('path')
@click.option('--filter-names', default=None,
              help='Read only playlists whose names matches this regex filter')
@click.option('--recursive', '-r', type=bool, is_flag=True, default=False,
              help='Search in subfolders.')
@click.option('--have-tags', default=None,
              help='Count only tracks that have all of the specified tags.')
@click.option('--have-no-tags', default=None,
              help='Count only tracks that do not have any of the listed tags.')
def local_count_tracks_in_playlists(path, filter_names, recursive, have_tags, have_no_tags):
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
            if have_tags is not None:
                have_tags_arr = have_tags.upper().split(',')
                if not spoty.local.check_track_have_all_tags(track, have_tags_arr):
                    continue

            if have_no_tags is not None:
                have__no_tags_arr = have_no_tags.upper().split(',')
                if spoty.local.check_track_have_all_tags(track, have__no_tags_arr):
                    continue

            all_tracks.append(track)

    click.echo(f'Found {len(all_tracks)} tracks in {len(playlists)} playlistss')


def print_duplicates_in_playlist(tags, duplicates_dic):
    i = 0
    for isrc, duplicates in duplicates_dic.items():
        i += 1
        click.echo(f"======================= DUPLICATE {i}/{len(duplicates_dic)} =============================")
        click.echo(f'{len(duplicates)} duplicates with "{",".join(tags)}" tags: {isrc}')
        click.echo("-----------------------------------------------------")
        for track in duplicates:
            click.echo(f'Track {track["SPOTY_PLAYLIST_INDEX"]} in playlist "{track["SPOTY_PLAYLIST_NAME"]}"')
            spoty.local.print_track_main_tags(track)


def print_duplicates_in_tracks(tags, duplicates_dic):
    i = 0
    for isrc, duplicates in duplicates_dic.items():
        i += 1
        click.echo(f"======================= DUPLICATE {i}/{len(duplicates_dic)} =============================")
        click.echo(f'{len(duplicates)} duplicates with "{",".join(tags)}" tags: {isrc}')
        click.echo("-----------------------------------------------------")
        for track in duplicates:
            click.echo(f'Track {track["SPOTY_FILE_NAME"]}"')
            spoty.local.print_track_main_tags(track)


def duplicates_from_dict_to_array(duplicates_dic):
    duplicates = []
    i = 0
    for tag, tracks in duplicates_dic.items():
        i += 1
        for track in tracks:
            track['SPOTY_DUPLICATE_GROUP'] = i
        duplicates.extend(tracks)
    return duplicates


@local.command("list-duplicates-in-playlists")
@click.argument('tags')
@click.argument('path')
@click.option('--filter-names', default=None,
              help='Read only playlists whose names matches this regex filter')
@click.option('--recursive', '-r', type=bool, is_flag=True, default=False,
              help='Search in subfolders.')
def local_list_duplicates_in_playlists(tags, path, filter_names, recursive):
    r"""Displays the list of duplicates found in local playlists.

    TAGS - Tags to compare

    PATH - Path to search files

    Examples:

        spoty local list-duplicates-in-playlists isrc "C:\Users\User\Downloads\music"

        spoty local list-duplicates-in-playlists "artist,title" -r "C:\Users\User\Downloads\music"

        spoty local list-duplicates-in-playlists --filter-names "^awesome" "C:\Users\User\Downloads\music"
    """

    path = os.path.abspath(path)
    tags_arr = tags.upper().split(',') if tags is not None else []
    duplicates_dic, all_tracks, skipped_tracks = spoty.local.find_duplicates_in_playlists(path, tags_arr, recursive,
                                                                                          filter_names)
    print_duplicates_in_playlist(tags_arr, duplicates_dic)

    click.echo(
        f'Total {len(duplicates_dic)} duplicates found in {len(all_tracks)} tracks ({len(skipped_tracks)} have no "{tags}" tags and skipped)')


@local.command("list-duplicates-in-tracks")
@click.argument('tags')
@click.argument('path')
@click.option('--filter-names', default=None,
              help='Include only files whose names matches this regex filter')
@click.option('--have-tags', default=None,
              help='Include only files that have all of the specified tags.')
@click.option('--have-no-tags', default=None,
              help='Include only files that do not have any of the listed tags.')
@click.option('--recursive', '-r', type=bool, is_flag=True, default=False,
              help='Search in subfolders.')
def local_list_duplicates_in_tracks(tags, path, filter_names, recursive, have_tags, have_no_tags):
    r"""Displays the list of duplicates found in local tracks.

    PATH - Path to search files

    TAGS - Tags to compare

    Examples:

        spoty local list-duplicates-in-tracks isrc "C:\Users\User\Downloads\music"

        spoty local list-duplicates-in-tracks "artist,title" -r "C:\Users\User\Downloads\music"
    """

    path = os.path.abspath(path)

    tags_arr = tags.upper().split(',') if tags is not None else []
    have_tags_arr = have_tags.upper().split(',') if have_tags is not None else []
    have_no_tags_arr = have_no_tags.upper().split(',') if have_no_tags is not None else []

    duplicates_dic, all_tracks, skipped_tracks \
        = spoty.local.find_duplicates_in_tracks(path, tags_arr, recursive, filter_names, have_tags_arr,
                                                have_no_tags_arr)
    print_duplicates_in_tracks(tags_arr, duplicates_dic)

    click.echo(
        f'Total {len(duplicates_dic)} duplicates found in {len(all_tracks)} tracks ({len(skipped_tracks)} have no "{tags}" tags and skipped)')


@local.command("collect-duplicates-in-playlists")
@click.argument('tags')
@click.argument('import-path')
@click.argument('export-file-name')
@click.option('--filter-names', default=None,
              help='Read only playlists whose names matches this regex filter')
@click.option('--recursive', '-r', type=bool, is_flag=True, default=False,
              help='Search in subfolders.')
def local_collect_duplicates_in_playlists(tags, import_path, export_file_name, filter_names, recursive):
    r"""Collect the list of duplicates found in local playlists and create new playlists with duplicates only.

    TAGS - Tags to compare

    IMPORT-PATH - Path to search files

    EXPORT-FILE-NAME - Path to search files

    Examples:

        spoty local collect-duplicates-in-playlists isrc "C:\Users\User\Downloads\import" "C:\Users\User\Downloads\duplicates.csv"

        spoty local collect-duplicates-in-playlists -r "artist,title" "C:\Users\User\Downloads\import" "C:\Users\User\Downloads\duplicates.csv"
    """

    import_path = os.path.abspath(import_path)
    export_file_name = os.path.abspath(export_file_name)

    tags_arr = tags.upper().split(',') if tags is not None else []
    duplicates_dic, all_tracks, skipped_tracks = spoty.local.find_duplicates_in_playlists(import_path, tags_arr,
                                                                                          recursive,
                                                                                          filter_names)
    duplicates = duplicates_from_dict_to_array(duplicates_dic)

    spoty.local.write_tracks_to_csv_file(duplicates, export_file_name)

    click.echo(
        f'{len(duplicates_dic)} duplicates found in {len(all_tracks)} tracks ({len(skipped_tracks)} have no "{tags}" tags and skipped) exported to "{export_file_name}"')


@local.command("collect-duplicates-in-tracks")
@click.argument('tags')
@click.argument('import-path')
@click.argument('export-file-name')
@click.option('--filter-names', default=None,
              help='Include only files whose names matches this regex filter')
@click.option('--have-tags', default=None,
              help='Include only files that have all of the specified tags.')
@click.option('--have-no-tags', default=None,
              help='Include only files that do not have any of the listed tags.')
@click.option('--recursive', '-r', type=bool, is_flag=True, default=False,
              help='Search in subfolders.')
def local_collect_duplicates_in_tracks(tags, import_path, export_file_name, filter_names, recursive, have_tags,
                                       have_no_tags):
    r"""Collect the list of duplicates found in local tracks and create new playlists with duplicates only.

    TAGS - Tags to compare

    IMPORT-PATH - Path to search files

    EXPORT-FILE-NAME - Path to search files

    Examples:

        spoty local collect-duplicates-in-tracks isrc "C:\Users\User\Downloads\import" "C:\Users\User\Downloads\duplicates.csv"

        spoty local collect-duplicates-in-tracks -r "artist,title" "C:\Users\User\Downloads\import" "C:\Users\User\Downloads\duplicates.csv"
    """

    import_path = os.path.abspath(import_path)
    export_file_name = os.path.abspath(export_file_name)

    tags_arr = tags.upper().split(',') if tags is not None else []
    have_tags_arr = have_tags.upper().split(',') if have_tags is not None else []
    have_no_tags_arr = have_no_tags.upper().split(',') if have_no_tags is not None else []

    duplicates_dic, all_tracks, skipped_tracks \
        = spoty.local.find_duplicates_in_tracks(import_path, tags_arr, recursive, filter_names, have_tags_arr,
                                                have_no_tags_arr)

    duplicates = duplicates_from_dict_to_array(duplicates_dic)

    spoty.local.write_tracks_to_csv_file(duplicates, export_file_name)

    click.echo(
        f'{len(duplicates_dic)} duplicates found in {len(all_tracks)} tracks ({len(skipped_tracks)} have no "{tags}" tags and skipped) exported to "{export_file_name}"')


@local.command("add-missing-tags-from-spotify-library")
# @click.argument('compare-by-tags')
# @click.argument('missing-tags')
@click.argument('export-path')
@click.option('--compare-tags', default='ARTIST,TITLE',
              help='Tags to compare')
@click.option('--filter-names', default=None,
              help='Read only playlists whose names matches this regex filter')
@click.option('--have-tags', default=None,
              help='Include only files that have all of the specified tags.')
@click.option('--have-no-tags', default=None,
              help='Include only files that do not have any of the listed tags.')
@click.option('--recursive', '-r', type=bool, is_flag=True, default=False,
              help='Search local files in subfolders.')
@click.option('--user-id', default=None, help='Get playlists of this user')
def local_add_tags_from_spotify_library(export_path, recursive, compare_tags, filter_names, have_tags, have_no_tags,
                                        user_id):
    r"""Read local files and try to found it in spotify user library. If found, read tags in spotify tracks and write to local files.

    EXPORT_PATH - Path to search local files

    Examples:

        spoty local add-missing-tags-from-spotify-library -r "C:\Users\User\Downloads\music"

        spoty local add-missing-tags-from-spotify-library -r "C:\Users\User\Downloads\music" --compare-tags "artist,title,album"

        spoty local add-missing-tags-from-spotify-library -r "C:\Users\User\Downloads\music" --filter-names "^awesome"
    """

    export_path = os.path.abspath(export_path)

    have_tags_arr = have_tags.upper().split(',') if have_tags is not None else []
    have_no_tags_arr = have_no_tags.upper().split(',') if have_no_tags is not None else []
    compare_tags_arr = compare_tags.upper().split(',') if compare_tags is not None else []

    import_tracks_tags = spoty.playlist.get_tags_from_spotify_library(filter_names, user_id)
    export_tracks_tags = spoty.local.get_tags_from_tracks(export_path, recursive, have_tags_arr, have_no_tags_arr)
    missing_tags = spoty.local.get_missing_tags_from_tracks(import_tracks_tags, export_tracks_tags, compare_tags_arr)
    for file_name, tags in missing_tags.items():
        spoty.local.write_tags(file_name, tags)

    click.echo(f'Edited tracks: {len(missing_tags)}/{len(export_tracks_tags)}')


@local.command("add-missing-tags-from-tracks")
@click.argument('import-path')
@click.argument('export-path')
@click.option('--compare-tags', default='ARTIST,TITLE',
              help='Tags to compare')
@click.option('--have-tags', default=None,
              help='Include only files that have all of the specified tags.')
@click.option('--have-no-tags', default=None,
              help='Include only files that do not have any of the listed tags.')
@click.option('--recursive', '-r', type=bool, is_flag=True, default=False,
              help='Search local files in subfolders.')
def local_add_tags_from_tracks(import_path, export_path, recursive, compare_tags, have_tags, have_no_tags):
    r"""Read local files and try to found it in another folder. If found, read tags in import folder and write to tracks in export folder.

    IMPORT-PATH - Path to search local files for reading tags

    EXPORT-PATH - Path to search local files for writing tags

    Examples:

        spoty local add-missing-tags-from-tracks -r "C:\Users\User\Downloads\import" "C:\Users\User\Downloads\export"

        spoty local add-missing-tags-from-tracks -r "C:\Users\User\Downloads\import" "C:\Users\User\Downloads\export" --compare-tags "artist,title,album"

        spoty local add-missing-tags-from-tracks -r "C:\Users\User\Downloads\import" "C:\Users\User\Downloads\export" --filter-names "^awesome"
    """

    import_path = os.path.abspath(import_path)
    export_path = os.path.abspath(export_path)

    have_tags_arr = have_tags.upper().split(',') if have_tags is not None else []
    have_no_tags_arr = have_no_tags.upper().split(',') if have_no_tags is not None else []
    compare_tags_arr = compare_tags.upper().split(',') if compare_tags is not None else []

    import_tracks_tags = spoty.local.get_tags_from_tracks(import_path, recursive, have_tags_arr, have_no_tags_arr)
    export_tracks_tags = spoty.local.get_tags_from_tracks(export_path, recursive, have_tags_arr, have_no_tags_arr)
    missing_tags = spoty.local.get_missing_tags_from_tracks(import_tracks_tags, export_tracks_tags, compare_tags_arr)
    for file_name, tags in missing_tags.items():
        spoty.local.write_tags(file_name, tags)

    click.echo(f'Edited tracks: {len(missing_tags)}/{len(export_tracks_tags)}')


@local.command("list-missing-tags-from-spotify-library")
# @click.argument('compare-by-tags')
# @click.argument('missing-tags')
@click.argument('export-path')
@click.option('--compare-tags', default='ARTIST,TITLE',
              help='Tags to compare')
@click.option('--filter-names', default=None,
              help='Read only playlists whose names matches this regex filter')
@click.option('--have-tags', default=None,
              help='Include only files that have all of the specified tags.')
@click.option('--have-no-tags', default=None,
              help='Include only files that do not have any of the listed tags.')
@click.option('--recursive', '-r', type=bool, is_flag=True, default=False,
              help='Search local files in subfolders.')
@click.option('--user-id', default=None, help='Get playlists of this user')
def local_list_tags_from_spotify_library(export_path, recursive, compare_tags, filter_names, have_tags, have_no_tags,
                                         user_id):
    r"""Read local files and try to found it in spotify user library. If found, read tags in spotify tracks and display missing tags in local files.

    EXPORT_PATH - Path to search local files

    Examples:

        spoty local list-missing-tags-from-spotify-library -r "C:\Users\User\Downloads\music"

        spoty local list-missing-tags-from-spotify-library -r "C:\Users\User\Downloads\music" --compare-tags "artist,title,album"

        spoty local list-missing-tags-from-spotify-library -r "C:\Users\User\Downloads\music" --filter-names "^awesome"
    """

    export_path = os.path.abspath(export_path)

    have_tags_arr = have_tags.upper().split(',') if have_tags is not None else []
    have_no_tags_arr = have_no_tags.upper().split(',') if have_no_tags is not None else []
    compare_tags_arr = compare_tags.upper().split(',') if compare_tags is not None else []

    import_tracks_tags = spoty.playlist.get_tags_from_spotify_library(filter_names, user_id)
    export_tracks_tags = spoty.local.get_tags_from_tracks(export_path, recursive, have_tags_arr, have_no_tags_arr)
    missing_tags = spoty.local.get_missing_tags_from_tracks(import_tracks_tags, export_tracks_tags, compare_tags_arr)
    for file_name, tags in missing_tags.items():
        click.echo(f'----------------------------------------------------')
        click.echo(f'Tags missing in "{file_name}":')
        for key, value in tags.items():
            click.echo(f'{key}: {value}')

    click.echo(f'----------------------------------------------------')
    click.echo(f'Total tracks have missing tags: {len(missing_tags)}/{len(export_tracks_tags)}')


@local.command("list-missing-tags-from-tracks")
@click.argument('import-path')
@click.argument('export-path')
@click.option('--compare-tags', default='ARTIST,TITLE',
              help='Tags to compare')
@click.option('--have-tags', default=None,
              help='Include only files that have all of the specified tags.')
@click.option('--have-no-tags', default=None,
              help='Include only files that do not have any of the listed tags.')
@click.option('--recursive', '-r', type=bool, is_flag=True, default=False,
              help='Search local files in subfolders.')
def local_list_tags_from_tracks(import_path, export_path, recursive, compare_tags, have_tags, have_no_tags):
    r"""Read local files and try to found it in another folder. If found, read tags in import folder and display missing tags in tracks from export folder.

    IMPORT-PATH - Path to search local files for reading tags

    EXPORT-PATH - Path to search local files for writing tags

    Examples:

        spoty local list-missing-tags-from-tracks -r "C:\Users\User\Downloads\import" "C:\Users\User\Downloads\export"

        spoty local list-missing-tags-from-tracks -r "C:\Users\User\Downloads\import" "C:\Users\User\Downloads\export" --compare-tags "artist,title,album"

        spoty local list-missing-tags-from-tracks -r "C:\Users\User\Downloads\import" "C:\Users\User\Downloads\export" --filter-names "^awesome"
    """

    import_path = os.path.abspath(import_path)
    export_path = os.path.abspath(export_path)

    have_tags_arr = have_tags.upper().split(',') if have_tags is not None else []
    have_no_tags_arr = have_no_tags.upper().split(',') if have_no_tags is not None else []
    compare_tags_arr = compare_tags.upper().split(',') if compare_tags is not None else []

    import_tracks_tags = spoty.local.get_tags_from_tracks(import_path, recursive, have_tags_arr, have_no_tags_arr)
    export_tracks_tags = spoty.local.get_tags_from_tracks(export_path, recursive, have_tags_arr, have_no_tags_arr)
    missing_tags = spoty.local.get_missing_tags_from_tracks(import_tracks_tags, export_tracks_tags, compare_tags_arr)
    for file_name, tags in missing_tags.items():
        click.echo(f'----------------------------------------------------')
        click.echo(f'Tags missing in "{file_name}":')
        for key, value in tags.items():
            click.echo(f'{key}: {value}')

    click.echo(f'----------------------------------------------------')
    click.echo(f'Total tracks have missing tags: {len(missing_tags)}/{len(export_tracks_tags)}')


@local.command("fix-invalid-track-tags")
@click.argument('path')
@click.option('--have-tags',  default=None,
              help='Include only files that have all of the specified tags.')
@click.option('--have-no-tags',  default=None,
              help='Include only files that do not have any of the listed tags.')
@click.option('--recursive', '-r', type=bool, is_flag=True, default=False,
              help='Search local files in subfolders.')
def local_fix_invalid_track_tags(path, recursive, have_tags, have_no_tags):
    r"""Read local files and try to found it in spotify user library. If found, read tags in spotify tracks and write to local files.

    PATH - Path to search local files

    Examples:

        spoty local fix-invalid-track-tags -r "C:\Users\User\Downloads\music"

        spoty local fix-invalid-track-tags -r "C:\Users\User\Downloads\music" --filter-names "^awesome"
    """

    path = os.path.abspath(path)

    have_tags_arr = have_tags.upper().split(',') if have_tags is not None else []
    have_no_tags_arr = have_no_tags.upper().split(',') if have_no_tags is not None else []

    edited_files, all_files = spoty.local.fix_invalid_track_tags(path, recursive, have_tags_arr, have_no_tags_arr)

    click.echo(f'Fixed tracks: {len(edited_files)}/{len(all_files)}')
