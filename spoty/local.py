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

tag_allies = [
    ['YEAR', 'DATE'],
    ['TRACK', 'TRACKNUMBER'],
    ['DISK', 'DISKNUMBER']
]

spoty_tags = \
    [
        'SPOTY_DUPLICATE_GROUP',
        'SPOTY_PLAYLIST_NAME',
        'SPOTY_PLAYLIST_INDEX',
        'SPOTY_FILE_NAME',
        'LENGTH'

    ]

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
        'SPOTIFY_TRACK_ID'  # spotify specific
        'SPOTIFY_RELEASE_ID',  # spotify specific
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
        'EXPLICIT'
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

def is_valid_path(path):
    return os.path.isdir(path)

def is_valid_file(path):
    return os.path.isfile(path)


def check_track_have_all_tags(track, tags):
    for tag in tags:
        if not tag in track:
            return False
    return True


def filter_tracks_which_have_all_tags(file_names, tags):
    filtered = []
    for file_name in file_names:
        track = read_track_tags(file_name)
        if check_track_have_all_tags(track, tags):
            filtered.append(file_name)
    return filtered


def filter_tracks_which_not_have_any_of_tags(file_names, tags):
    filtered = []
    for file_name in file_names:
        track = read_track_tags(file_name)
        if not check_track_have_all_tags(track, tags):
            filtered.append(file_name)
    return filtered


def get_local_tracks_file_names(path,
                                recursive=True,
                                filter_names=None,
                                filter_have_tags=[],
                                filter_have_no_tags=[],
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
    if len(filter_have_tags) > 0:
        full_file_names = filter_tracks_which_have_all_tags(full_file_names, filter_have_tags)

    if len(filter_have_no_tags) > 0:
        full_file_names = filter_tracks_which_not_have_any_of_tags(full_file_names, filter_have_no_tags)

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


def read_tracks_tags(track_file_names, add_file_name=False):
    tracks = []
    for file_name in track_file_names:
        track = read_track_tags(file_name, add_file_name)
        tracks.append(track)
    return tracks


def read_track_tags(file_name, add_file_name=False):
    track = {}

    if add_file_name:
        track['SPOTY_FILE_NAME'] = file_name

    if is_flac(file_name):
        f = None
        try:
            f = FLAC(file_name)
        except:
            time.sleep(0.2)
            click.echo(f"\nCant open file: {file_name}")
            return []
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

        track['LENGTH'] = str(int(f.info.length * 1000))
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

    # reorder spoty tags first
    for key in spoty_tags:
        if key in keys:
            res.append(key)

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





def find_duplicates_in_tag_tracks(all_tracks, tags_to_compare):
    if len(tags_to_compare) == 0:
        return

    duplicates = {}
    pattern = ""
    for tag in tags_to_compare:
        pattern += "%" + tag + "%,"
    pattern = pattern[:-1]

    groupped_tracks = group_tracks_by_pattern(pattern, all_tracks, "Unknown")

    for tags, tracks in groupped_tracks.items():
        if tags == "Unknown":
            continue
        if len(tracks) > 1:
            if not tags in duplicates:
                duplicates[tags] = []
            duplicates[tags].extend(tracks)

    skipped_tracks = groupped_tracks['Unknown'] if 'Unknown' in groupped_tracks else []

    return duplicates, all_tracks, skipped_tracks


def find_duplicates_in_playlists(path, tags_to_compare, recursive=True, filter_names=None):
    all_tracks = []

    playlists = spoty.local.get_all_playlists_in_path(path, recursive, filter_names)
    for file_name in playlists:
        tracks = spoty.local.read_tracks_from_csv_file(file_name, True)
        all_tracks.extend(tracks)

    duplicates, all_tracks, skipped_tracks = find_duplicates_in_tag_tracks(all_tracks, tags_to_compare)

    return duplicates, all_tracks, skipped_tracks


def find_duplicates_in_tracks(path,
                              tags_to_compare,
                              recursive=True,
                              filter_names=None,
                              filter_have_tags=[],
                              filter_have_no_tags=[]):
    if len(tags_to_compare) == 0:
        return

    full_file_names = spoty.local.get_local_tracks_file_names(path, recursive, filter_names, filter_have_tags,
                                                              filter_have_no_tags)
    all_tracks = read_tracks_tags(full_file_names, True)
    duplicates, all_tracks, skipped_tracks = find_duplicates_in_tag_tracks(all_tracks, tags_to_compare)

    return duplicates, all_tracks, skipped_tracks


def get_tags_from_tracks(import_path, recursive, have_tags, have_no_tags):
    import_directories = []
    for (dirpath, dirnames, filenames) in os.walk(import_path):
        import_directories.append(dirpath)
        if not recursive:
            break

    tracks_tags = []

    with click.progressbar(import_directories, label='Reading tracks from local files') as bar:
        for dir in bar:
            tracks_file_names = \
                spoty.local.get_local_tracks_file_names(dir, False, None, have_tags, have_no_tags)

            if len(tracks_file_names) == 0:
                continue

            tags = spoty.local.read_tracks_tags(tracks_file_names, True)
            tracks_tags.extend(tags)

    return tracks_tags


def get_missing_tags_from_tracks(import_tracks_tags, export_tracks_tags, compare_tags):
    missing_tags = {}
    with click.progressbar(import_tracks_tags, label='Searching missing tags in files') as bar:
        for import_tags in bar:
            for export_tags in export_tracks_tags:
                if spoty.utils.compare_two_tag_tracks(import_tags, export_tags, compare_tags):
                    file_name = export_tags['SPOTY_FILE_NAME']
                    tags = get_missing_tags(file_name, import_tags)
                    if len(tags) > 0:
                        missing_tags[file_name] = tags
    return missing_tags


def write_missing_tags_from_tracks(import_tracks_tags, export_tracks_tags, compare_tags):
    edited_files = []
    with click.progressbar(import_tracks_tags, label='Writing missing tags to files') as bar:
        for import_tags in bar:
            for export_tags in export_tracks_tags:
                if spoty.utils.compare_two_tag_tracks(import_tags, export_tags, compare_tags):
                    file_name = export_tags['SPOTY_FILE_NAME']
                    missing_tags = get_missing_tags(file_name, import_tags)
                    if len(missing_tags) > 0:
                        write_tags(file_name, missing_tags)
                        edited_files.append(file_name)
                        # click.echo(f'Added {str(added_tags)} to {file_name}')
                        # log.debug(f'Added {str(added_tags)} to {file_name}')
    return edited_files, export_tracks_tags


def get_missing_tags(file_name, new_tags):
    missing_tags = {}

    exist_tags = read_track_tags(file_name)

    for key, value in new_tags.items():
        if key == 'LENGTH':
            continue

        if key in spoty_tags:
            continue

        if key in exist_tags:
            continue

        found = False
        for aliases in tag_allies:
            if key in aliases:
                for al in aliases:
                    if al in exist_tags:
                        found = True
        if found:
            continue

        missing_tags[key] = value
    return missing_tags


def write_tags(file_name, new_tags):
    if len(new_tags) > 0:
        if is_flac(file_name):
            f = FLAC(file_name)
            for key, value in new_tags.items():
                f[key] = str(value)
            f.save()


def fix_invalid_track_tags(path, recursive, have_tags, have_no_tags):
    directories = []
    for (dirpath, dirnames, filenames) in os.walk(path):
        directories.append(dirpath)
        if not recursive:
            break

    local_tracks_file_names = []
    local_tracks_tags = []

    with click.progressbar(directories, label='Collecting tracks') as bar:
        for dir in bar:
            tracks_file_names = \
                spoty.local.get_local_tracks_file_names(dir, False, None, have_tags, have_no_tags)

            if len(tracks_file_names) == 0:
                continue

            local_tracks_file_names.extend(tracks_file_names)
            tags = spoty.local.read_tracks_tags(tracks_file_names, True)
            local_tracks_tags.extend(tags)

    edited_files = []

    replace_comma = []
    for track in local_tracks_tags:
        if ',' in track['ARTIST']:
            replace_comma.append(track)

    if len(replace_comma) > 0:
        for track in replace_comma:
            file_name = track['SPOTY_FILE_NAME']
            click.echo(f'ARTIST: "{track["ARTIST"]}" in "{file_name}"')
        click.echo(f'Total tracks: {len(replace_comma)}')
        if (click.confirm("Do you want to replace ',' to ';' in this tracks?")):
            for track in replace_comma:
                file_name = track['SPOTY_FILE_NAME']
                f = FLAC(file_name)
                artists = f.tags['ARTIST']
                for i in range(len(artists)):
                    artists[i] = artists[i].replace(',', ';')
                f['ARTIST'] = artists
                f.save()
                if track not in edited_files:
                    edited_files.append(track)

    return edited_files, local_tracks_file_names
