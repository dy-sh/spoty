from spoty import sp
from spoty import log
import spoty.utils
import spoty.like
import os.path
import click
import time
import re
import mutagen
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
import csv

main_tags = \
    [
        'ISRC',
        'ARTIST',
        'ALBUMARTIST',
        'TITLE',
        'ALBUM',
        'GENRE',
        'MOOD',
        'OCCASION',
        'RATING',
        'COMMENT'
        'BARCODE',
        'BPM',
        'FILEOWNER'  # public
        'LENGTH',
        'QUALITY',
        'SPOTIFY_RELEASE_ID',  # spotify specific
        'SPOTIFY_TRACK_ID'  # spotify specific
        'SOURCE',  # deezer specific
        'SOURCEID',  # deezer specific
        'TEMPO',
        'YEAR',
    ]

additional_tags = \
    [
        '1T_TAGGEDDATE',  # auto tagger
        'AUTHOR',
        'COMPILATION',
        'COMPOSER',
        'COPYRIGHT',
        'DISC',
        'ENCODER',
        'INITIAL KEY',
        'INITIALKEY'
        'ENGINEER',
        'INVOLVEDPEOPLE',
        'ITUNESADVISORY',
        'LABEL',
        'LOVE RATING',
        'LYRICS',
        'MIXER',
        'PRODUCER',
        'PUBLISHER',
        'REPLAYGAIN_TRACK_GAIN',
        'RELEASE DATE'
        'STYLE',
        'TOTALDISCS',
        'TOTALTRACKS',
        'TRACK',
        'UPC',
        'WRITER',
    ]


class CSVImportException(Exception):
    """Base class for exceptions when importing CSV file."""
    pass


class CSVFileEmpty(CSVImportException):
    """File is empty."""
    pass


class CSVFileInvalidHeader(CSVImportException):
    """The header of csv table does not contain any of the required fields."""
    pass


def is_flac(file_name):
    return file_name.upper().endswith('.FLAC')


def is_mp3(file_name):
    return file_name.upper().endswith('.MP3')


def is_csv(file_name):
    return file_name.upper().endswith('.CSV')


def get_local_tracks_file_names(path,
                                recursive=True,
                                filter_names=None,
                                filter_have_isrc=False,
                                filter_have_no_isrc=False,
                                ):
    full_file_names = []
    if recursive:
        full_file_names = [os.path.join(dp, f) for dp, dn, filenames in os.walk(path) for f in filenames if
                           is_flac(os.path.splitext(f)[1]) or is_mp3(os.path.splitext(f)[1])]
    else:
        full_file_names = [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        full_file_names = list(
            filter(lambda f: is_flac(f) or is_mp3(f), full_file_names))

    if filter_names is not None:
        full_file_names = list(filter(lambda f:
                                      re.findall(filter_names, os.path.basename(f)),
                                      full_file_names))
    if filter_have_isrc:
        filtered = []
        for file_name in full_file_names:
            tags = read_track_tags(file_name)
            if len(tags['ISRC']) > 0:
                filtered.append(file_name)
            full_file_names = filtered

    if filter_have_no_isrc:
        filtered = []
        for file_name in full_file_names:
            tags = read_track_tags(file_name)
            if len(tags['ISRC']) == 0:
                filtered.append(file_name)
            full_file_names = filtered

    return full_file_names


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


def read_tracks_tags(track_file_names):
    tracks = []
    for file_name in track_file_names:
        track = read_track_tags(file_name)
        tracks.append(track)
    return tracks


def read_track_tags(file_name):
    track = {}

    if is_flac(file_name):
        f = FLAC(file_name)
        for tag in f.tags:
            if len(tag[1]) > 131072 or \
                    (tag[0] in track and len(track[tag[0]]) + len(tag[1]) > 131072):
                time.sleep(0.2)
                mess = f'Tag "{tag[0]}" has value larger than csv field limit (131072) and will be skipped in file "{file_name}"'
                click.echo('\n' + mess)
                log.warning(mess)
                continue
            if tag[0] in track:
                track[tag[0]] += ';' + tag[1]
            else:
                track[tag[0]] = tag[1]
        # for tag in main_tags:
        #     track[tag] = ",".join(f.tags[tag]) if tag in f.tags else ""
        # for tag in additional_tags:
        #     track[tag] = ",".join(f.tags[tag]) if tag in f.tags else ""

    return track


def collect_playlist_from_files(playlist_file_name, track_file_names, overwrite=False):
    log.info(f'Exporting playlist (tracks:{len(track_file_names)}, file name: {playlist_file_name})')

    if os.path.isfile(playlist_file_name) and not overwrite:
        time.sleep(0.2)  # waiting progressbar updating
        if not click.confirm(f'\nFile "{playlist_file_name}" already exist. Overwrite?'):
            log.info(f'Canceled by user (file already exist)')
            return None

    tracks = read_tracks_tags(track_file_names)

    write_tracks_to_csv_file(tracks, playlist_file_name)
    #
    # log.success(f'Playlist {playlist_id} exported (file: "{file_name}")')
    #
    return tracks


def reorder_tag_keys(keys):
    res = []

    # reorder main tags first
    for key in main_tags:
        if key in keys:
            res.append(key)

    # add other tags
    for key in keys:
        if not key in res:
            res.append(key)

    return res


def group_tracks_by_pattern(pattern, tracks, not_found_tag_name="Unknown"):
    groups = {}

    for track in tracks:
        group_name = ""
        tag_name = ""
        building_tag = False
        for c in pattern:
            if c == "%":
                building_tag = not building_tag
                if not building_tag:
                    tag = track[tag_name] if tag_name in track else not_found_tag_name
                    group_name += tag
                    tag_name = ""
            else:
                if building_tag:
                    tag_name += c
                    tag_name = tag_name.upper()
                else:
                    group_name += c

        if not group_name in groups:
            groups[group_name] = []

        groups[group_name].append(track)

    return groups


def write_tracks_to_csv_file(tracks, playlist_file_name):
    # collect all keys
    keys = []
    for track in tracks:
        for key, value in track.items():
            if not key in keys:
                keys.append(key)

    keys = reorder_tag_keys(keys)

    # write missing keys to all tracks
    for track in tracks:
        for key in keys:
            if not key in track:
                track[key] = ""

    os.makedirs(os.path.dirname(playlist_file_name), exist_ok=True)
    with open(playlist_file_name, 'w', encoding='utf-8-sig', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(keys)

        for track in tracks:
            values = [track[key] for key in keys]
            writer.writerow(values)


def read_tracks_from_csv_file(playlist_file_name):
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
            for h, key in enumerate(header):
                if len(row[h]) > 0:
                    track[key] = row[h]

            tracks.append(track)

    return tracks
