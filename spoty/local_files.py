from spoty import log
import spoty.utils
import os.path
import click
import time
import re
from mutagen.flac import FLAC


# from mutagen.mp3 import MP3
# from mutagen.id3 import ID3

def is_flac(file_name):
    return file_name.upper().endswith('.FLAC')


def is_mp3(file_name):
    return file_name.upper().endswith('.MP3')


def find_audio_files_in_paths(audio_files_paths, recursive, filter_have_tags=None, filter_have_no_tags=None):
    all_file_names = []

    for path in audio_files_paths:
        file_names = find_audio_files_in_path(path, recursive, filter_have_tags, filter_have_no_tags)
        all_file_names.extend(file_names)

    return all_file_names


def find_audio_files_in_path(audio_files_path, recursive=False, filter_have_tags=None, filter_have_no_tags=None):
    audio_files_path = os.path.abspath(audio_files_path)
    file_names = []

    if recursive:
        file_names = [os.path.join(dp, f) for dp, dn, filenames in os.walk(audio_files_path) for f in filenames if
                      is_flac(os.path.splitext(f)[1]) or is_mp3(os.path.splitext(f)[1])]
    else:
        file_names = [os.path.join(audio_files_path, f) for f in os.listdir(audio_files_path) if
                      os.path.isfile(os.path.join(audio_files_path, f))]
        file_names = list(
            filter(lambda f: is_flac(f) or is_mp3(f), file_names))

    if len(filter_have_tags) > 0:
        file_names = filter_tracks_which_have_all_tags(file_names, filter_have_tags)

    if len(filter_have_no_tags) > 0:
        file_names = filter_tracks_which_not_have_any_of_tags(file_names, filter_have_no_tags)

    return file_names


def filter_tracks_which_have_all_tags(file_names, tags):
    filtered = []
    for file_name in file_names:
        track = read_local_audio_track_tags(file_name)
        if spoty.utils.check_track_have_all_tags(track, tags):
            filtered.append(file_name)
    return filtered


def filter_tracks_which_not_have_any_of_tags(file_names, tags):
    filtered = []
    for file_name in file_names:
        track = read_local_audio_track_tags(file_name)
        if not spoty.utils.check_track_have_all_tags(track, tags):
            filtered.append(file_name)
    return filtered


def get_local_tracks_file_names_old(path,
                                    recursive=True,
                                    filter_names: list = None,
                                    filter_have_tags=None,
                                    filter_have_no_tags=None,
                                    ):
    full_file_names = []
    if filter_have_tags is None:
        filter_have_tags = []

    if filter_have_no_tags is None:
        filter_have_no_tags = []

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


def read_local_audio_tracks_tags(track_file_names, add_extra_info=True):
    tracks = []
    for file_name in track_file_names:
        track = read_local_audio_track_tags(file_name, add_extra_info)
        tracks.append(track)
    return tracks


def read_local_audio_track_tags(file_name, add_extra_info=True):
    track = {}

    file_name = os.path.abspath(file_name)

    if add_extra_info:
        dir = os.path.dirname(file_name)
        track['SPOTY_FILE_NAME'] = file_name
        track['SPOTY_PLAYLIST_SOURCE'] = "LOCAL"
        track['SPOTY_PLAYLIST_NAME'] = os.path.basename(os.path.normpath(dir))

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


def find_duplicates_in_tracks(path,
                              tags_to_compare,
                              recursive=True,
                              filter_names=None,
                              filter_have_tags=None,
                              filter_have_no_tags=None):
    if len(tags_to_compare) == 0:
        return

    if filter_have_tags is None:
        filter_have_tags = []

    if filter_have_no_tags is None:
        filter_have_no_tags = []

    full_file_names = get_local_tracks_file_names_old(path, recursive, filter_names, filter_have_tags,
                                                      filter_have_no_tags)
    all_tracks = read_local_audio_tracks_tags(full_file_names, True)
    duplicates, all_tracks, skipped_tracks = spoty.utils.find_duplicates_in_tag_tracks(all_tracks, tags_to_compare)

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
                get_local_tracks_file_names_old(dir, False, None, have_tags, have_no_tags)

            if len(tracks_file_names) == 0:
                continue

            tags = read_local_audio_tracks_tags(tracks_file_names, True)
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

    exist_tags = read_local_audio_track_tags(file_name)

    for key, value in new_tags.items():
        if key == 'LENGTH':
            continue

        if key in spoty.utils.spoty_tags:
            continue

        if key in exist_tags:
            continue

        found = False
        for aliases in spoty.utils.tag_allies:
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
                get_local_tracks_file_names_old(dir, False, None, have_tags, have_no_tags)

            if len(tracks_file_names) == 0:
                continue

            local_tracks_file_names.extend(tracks_file_names)
            tags = read_local_audio_tracks_tags(tracks_file_names, True)
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
