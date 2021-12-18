from spoty import log
import spoty.spotify
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
    r"""Local files management."""
    pass


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

    playlists = spoty.csv_playlist.find_csvs_in_path(path, recursive, filter_names)
    for file_name in playlists:
        tracks = spoty.csv_playlist.read_tags_from_csv(file_name)

        for track in tracks:
            if have_tags is not None:
                have_tags_arr = have_tags.upper().split(',')
                if not spoty.utils.check_all_tags_exist(track, have_tags_arr):
                    continue

            if have_no_tags is not None:
                have__no_tags_arr = have_no_tags.upper().split(',')
                if spoty.utils.check_all_tags_exist(track, have__no_tags_arr):
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
            spoty.utils.print_main_tags(track)


def print_duplicates_in_tracks(tags, duplicates_dic):
    i = 0
    for isrc, duplicates in duplicates_dic.items():
        i += 1
        click.echo(f"======================= DUPLICATE {i}/{len(duplicates_dic)} =============================")
        click.echo(f'{len(duplicates)} duplicates with "{",".join(tags)}" tags: {isrc}')
        click.echo("-----------------------------------------------------")
        for track in duplicates:
            click.echo(f'Track {track["SPOTY_FILE_NAME"]}"')
            spoty.utils.print_main_tags(track)


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
    duplicates_dic, all_tracks, skipped_tracks = spoty.csv_playlist.find_duplicates_in_csvs(path, tags_arr, recursive,
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
        = spoty.audio_files.find_duplicates_in_audio_files(path, tags_arr, recursive, filter_names, have_tags_arr,
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
    duplicates_dic, all_tracks, skipped_tracks = spoty.csv_playlist.find_duplicates_in_csvs(import_path, tags_arr,
                                                                                            recursive,
                                                                                            filter_names)
    duplicates = duplicates_from_dict_to_array(duplicates_dic)

    spoty.csv_playlist.write_tags_to_csv(duplicates, export_file_name)

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
        = spoty.audio_files.find_duplicates_in_audio_files(import_path, tags_arr, recursive, filter_names,
                                                           have_tags_arr,
                                                           have_no_tags_arr)

    duplicates = duplicates_from_dict_to_array(duplicates_dic)

    spoty.csv_playlist.write_tags_to_csv(duplicates, export_file_name)

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

    import_tracks_tags = spoty.spotify.get_tags_from_spotify_library(filter_names, user_id)
    audio_files_names = spoty.audio_files.find_audio_files_in_path(
        export_path, recursive, have_tags_arr, have_no_tags_arr)
    export_tracks_tags = spoty.audio_files.read_audio_files_tags(audio_files_names)
    missing_tags = spoty.audio_files.get_missing_tags_from_source_to_dest_audio_files(
        import_tracks_tags, export_tracks_tags, compare_tags_arr)
    for file_name, tags in missing_tags.items():
        spoty.audio_files.write_audio_file_tags(file_name, tags)

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

    audio_files_names = spoty.audio_files.find_audio_files_in_path(import_path, recursive, have_tags_arr,
                                                                   have_no_tags_arr)
    import_tracks_tags = spoty.audio_files.read_audio_files_tags(audio_files_names)
    audio_files_names = spoty.audio_files.find_audio_files_in_path(export_path, recursive, have_tags_arr,
                                                                   have_no_tags_arr)
    export_tracks_tags = spoty.audio_files.read_audio_files_tags(audio_files_names)

    missing_tags = spoty.audio_files.get_missing_tags_from_source_to_dest_audio_files(import_tracks_tags,
                                                                                      export_tracks_tags,
                                                                                      compare_tags_arr)
    for file_name, tags in missing_tags.items():
        spoty.audio_files.write_audio_file_tags(file_name, tags)

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

    import_tracks_tags = spoty.spotify.get_tags_from_spotify_library(filter_names, user_id)
    audio_files_names = spoty.audio_files.find_audio_files_in_path(export_path, recursive, have_tags_arr,
                                                                   have_no_tags_arr)
    export_tracks_tags = spoty.audio_files.read_audio_files_tags(audio_files_names)
    missing_tags = spoty.audio_files.get_missing_tags_from_source_to_dest_audio_files(import_tracks_tags,
                                                                                      export_tracks_tags,
                                                                                      compare_tags_arr)
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

    audio_files_names = spoty.audio_files.find_audio_files_in_path(import_path, recursive, have_tags_arr,
                                                                   have_no_tags_arr)
    import_tracks_tags = spoty.audio_files.read_audio_files_tags(audio_files_names)
    audio_files_names = spoty.audio_files.find_audio_files_in_path(export_path, recursive, have_tags_arr,
                                                                   have_no_tags_arr)
    export_tracks_tags = spoty.audio_files.read_audio_files_tags(audio_files_names)
    missing_tags = spoty.audio_files.get_missing_tags_from_source_to_dest_audio_files(import_tracks_tags,
                                                                                      export_tracks_tags,
                                                                                      compare_tags_arr)
    for file_name, tags in missing_tags.items():
        click.echo(f'----------------------------------------------------')
        click.echo(f'Tags missing in "{file_name}":')
        for key, value in tags.items():
            click.echo(f'{key}: {value}')

    click.echo(f'----------------------------------------------------')
    click.echo(f'Total tracks have missing tags: {len(missing_tags)}/{len(export_tracks_tags)}')


@local.command("fix-invalid-track-tags")
@click.argument('path')
@click.option('--have-tags', default=None,
              help='Include only files that have all of the specified tags.')
@click.option('--have-no-tags', default=None,
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

    edited_files, all_files = spoty.audio_files.fix_invalid_audio_file_tags(path, recursive, have_tags_arr,
                                                                            have_no_tags_arr)

    click.echo(f'Fixed tracks: {len(edited_files)}/{len(all_files)}')
