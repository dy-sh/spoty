from spoty import log
import spoty.utils
import spoty.local
import click
import os
import csv
import time
import re


class CSVImportException(Exception):
    """Base class for exceptions when importing CSV file."""
    pass


class CSVFileEmpty(CSVImportException):
    """File is empty."""
    pass


class CSVFileInvalidHeader(CSVImportException):
    """The header of csv table does not contain any of the required fields."""
    pass


def is_csv(file_name):
    return file_name.upper().endswith('.CSV')


def export_tags(all_tags, export_path, export_naming_pattern, overwrite):
    exported_playlists_file_names = []
    exported_playlists_names = []
    exported_tracks = []

    if len(all_tags) > 0:
        grouped_tracks = spoty.utils.group_tracks_by_pattern(export_naming_pattern, all_tags)

        for group, tracks in grouped_tracks.items():
            playlist_name = group
            playlist_name = spoty.utils.slugify_file_pah(playlist_name)
            playlist_file_name = os.path.join(export_path, playlist_name + '.csv')

            if playlist_file_name in exported_playlists_file_names:
                write_tracks_to_csv_file(tracks, playlist_file_name, True)
            else:
                if os.path.isfile(playlist_file_name) and not overwrite:
                    if not click.confirm(f'File "{playlist_file_name}" already exist. Overwrite?'):
                        continue

                write_tracks_to_csv_file(tracks, playlist_file_name, False)

            exported_playlists_names.append(playlist_name)
            exported_playlists_file_names.append(playlist_file_name)
            exported_tracks.extend(tracks)

        mess = f'\n{len(exported_tracks)} tracks exported to {len(exported_playlists_file_names)} playlists in path: "{export_path}"'
        click.echo(mess)

    return exported_playlists_file_names, exported_playlists_names, exported_tracks


def get_all_playlists_in_path(path,
                              recursive=True,
                              filter_names=None
                              ):
    full_file_names = []
    if recursive:
        full_file_names = [os.path.join(dp, f) for dp, dn, filenames in os.walk(path) for f in filenames if
                           is_csv(os.path.splitext(f)[1])]
    else:
        full_file_names = [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        full_file_names = list(filter(lambda f: is_csv(f), full_file_names))

    if filter_names is not None:
        full_file_names = list(filter(lambda f:
                                      re.findall(filter_names, os.path.basename(f)),
                                      full_file_names))

    return full_file_names


def write_tracks_to_csv_file(tracks, playlist_file_name, append=False):
    # collect all keys
    keys = []
    for track in tracks:
        for key, value in track.items():
            if not key in keys:
                keys.append(key)

    keys = spoty.utils.reorder_tag_keys(keys)

    # write missing keys to all tracks
    for track in tracks:
        for key in keys:
            if not key in track:
                track[key] = ""

    os.makedirs(os.path.dirname(playlist_file_name), exist_ok=True)

    method = 'w'
    if append:
        if os.path.isfile(playlist_file_name):
            with open(playlist_file_name, newline='', encoding='utf-8-sig') as file:
                reader = csv.reader(file)
                if sum(1 for row in reader) != 0:  # file is not empty
                    method = 'a'

    with open(playlist_file_name, method, encoding='utf-8-sig', newline='') as file:
        writer = csv.writer(file)

        if method == 'w':  # write header to new file
            writer.writerow(keys)

        for track in tracks:
            values = [track[key] for key in keys]
            writer.writerow(values)


def read_tracks_from_csv_file(playlist_file_name, add_playlist_info=False):
    tracks = []

    with open(playlist_file_name, newline='', encoding='utf-8-sig') as file:
        reader = csv.reader(file)
        if sum(1 for row in reader) == 0:
            raise CSVFileEmpty()

    with open(playlist_file_name, newline='', encoding='utf-8-sig') as file:
        header = []
        reader = csv.reader(file)

        for i, row in enumerate(reader):
            # read header
            if (i == 0):
                header = row
                if len(header) == 0:
                    raise CSVFileInvalidHeader()
                continue

            # read track
            if len(row) == 0:
                continue

            track = {}

            if (add_playlist_info):
                track['SPOTY_PLAYLIST_NAME'] = playlist_file_name
                track['SPOTY_PLAYLIST_INDEX'] = i - 1

            for h, key in enumerate(header):
                if len(row[h]) > 0:
                    track[key] = row[h]

            tracks.append(track)

    return tracks


def collect_playlist_from_files(playlist_file_name, track_file_names, overwrite=False):
    log.info(f'Exporting playlist (tracks:{len(track_file_names)}, file name: {playlist_file_name})')

    if os.path.isfile(playlist_file_name) and not overwrite:
        time.sleep(0.2)  # waiting progressbar updating
        if not click.confirm(f'\nFile "{playlist_file_name}" already exist. Overwrite?'):
            log.info(f'Canceled by user (file already exist)')
            return None

    tracks = spoty.local.read_local_audio_tracks_tags(track_file_names)

    write_tracks_to_csv_file(tracks, playlist_file_name)
    #
    # log.success(f'Playlist {playlist_id} exported (file: "{file_name}")')
    #
    return tracks


def find_duplicates_in_playlists(path, tags_to_compare, recursive=True, filter_names=None):
    all_tracks = []

    playlists = spoty.csv_playlist.get_all_playlists_in_path(path, recursive, filter_names)
    for file_name in playlists:
        tracks = spoty.csv_playlist.read_tracks_from_csv_file(file_name, True)
        all_tracks.extend(tracks)

    duplicates, all_tracks, skipped_tracks = spoty.utils.find_duplicates_in_tag_tracks(all_tracks, tags_to_compare)

    return duplicates, all_tracks, skipped_tracks
