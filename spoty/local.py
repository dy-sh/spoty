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


def is_flac(file_name):
    return file_name.upper().endswith('.FLAC')


def is_mp3(file_name):
    return file_name.upper().endswith('.MP3')


def get_local_tracks_file_names(path,
                                recursive=True,
                                filter_names=None,
                                filter_have_isrc=False,
                                filter_have_no_isrc=False,
                                ):
    full_file_names = []
    if recursive:
        full_file_names = [os.path.join(dp, f) for dp, dn, filenames in os.walk(path) for f in filenames if
                           os.path.splitext(f)[1] == '.flac' or os.path.splitext(f)[1] == '.mp3']
    else:
        full_file_names = [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        full_file_names = list(filter(lambda f: f.endswith('.flac') or f.endswith('.mp3'), full_file_names))

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


def read_tracks_tags(track_file_names):
    tracks = []
    for file_name in track_file_names:
        track = read_track_tags(file_name)
        tracks.append(track)
    return tracks


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


def read_track_tags(file_name):
    track = {}

    if is_flac(file_name):
        f = FLAC(file_name)
        for tag in f.tags:
            if tag[0] in track:
                track[tag[0]] += ';' + tag[1]
            else:
                track[tag[0]] = tag[1]
        # for tag in main_tags:
        #     track[tag] = ",".join(f.tags[tag]) if tag in f.tags else ""
        # for tag in additional_tags:
        #     track[tag] = ",".join(f.tags[tag]) if tag in f.tags else ""

    return track


def export_playlist_to_file(playlist_file_name, track_file_names, overwrite=False):
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


def write_tracks_to_csv_file(tracks, file_name):
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

    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    with open(file_name, 'w', encoding='utf-8-sig', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(keys)

        for track in tracks:
            values = [track[key] for key in keys]
            writer.writerow(values)


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


def group_tracks_by_pattern(pattern, tracks):
    groups = {}

    for track in tracks:
        group_name = ""
        tag_name = ""
        building_tag = False
        for c in pattern:
            if c == "%":
                building_tag = not building_tag
                if not building_tag:
                    tag = track[tag_name] if tag_name in track else "Unknown"
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
