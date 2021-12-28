from spoty import log
import spoty.utils
import os.path
import click
import time, datetime
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3


def is_flac(file_name):
    return file_name.upper().endswith('.FLAC')


def is_mp3(file_name):
    return file_name.upper().endswith('.MP3')


def is_audio_file(file_name):
    return is_flac(file_name) or is_mp3(file_name)


def find_audio_files_in_paths(paths, recursive=True):
    all_file_names = []

    for path in paths:
        file_names = find_audio_files_in_path(path, recursive)
        all_file_names.extend(file_names)

    return all_file_names


def find_audio_files_in_path(path, recursive=True):
    path = os.path.abspath(path)

    if not spoty.utils.is_valid_path(path):
        raise Exception("Path is not valid: " + path)

    file_names = []

    if recursive:
        file_names = [os.path.join(dp, f) for dp, dn, filenames in os.walk(path) for f in filenames if
                      is_flac(os.path.splitext(f)[1]) or is_mp3(os.path.splitext(f)[1])]
    else:
        file_names = [os.path.join(path, f) for f in os.listdir(path) if
                      os.path.isfile(os.path.join(path, f))]
        file_names = list(
            filter(lambda f: is_flac(f) or is_mp3(f), file_names))

    return file_names


def write_audio_file_tags(file_name, new_tags):
    if len(new_tags) > 0:
        if is_flac(file_name):
            f = FLAC(file_name)
            for key, value in new_tags.items():
                f[key] = str(value)
            f.save()
        if is_mp3(file_name):
            f = EasyID3(file_name)
            for key, value in new_tags.items():
                if key not in f.valid_keys:
                    click.echo(f'MP3 tag {key} is not valid tag')
                f[key.lower()] = str(value)
            f.save(v2_version=3)


def read_audio_files_tags(file_names, add_spoty_tags=True):
    tags_list = []
    with click.progressbar(file_names, label=f'Reading tags in {len(file_names)} files') as bar:
        for file_name in bar:
            tags = read_audio_file_tags(file_name, add_spoty_tags)
            if tags is not None:
                tags_list.append(tags)
    return tags_list


def read_audio_file_tags(file_name, add_spoty_tags=True):
    tags = {}

    file_name = os.path.abspath(file_name)

    if add_spoty_tags:
        dir = os.path.dirname(file_name)
        tags['SPOTY_FILE_NAME'] = file_name
        tags['SPOTY_SOURCE'] = "LOCAL"
        tags['SPOTY_PLAYLIST_NAME'] = os.path.basename(os.path.normpath(dir))
        tags['SPOTY_TRACK_ADDED'] =  datetime.datetime.fromtimestamp(os.path.getctime(file_name)).strftime('%Y-%m-%d %H:%M:%S')

    if is_flac(file_name):
        try:
            f = FLAC(file_name)
            tags['SPOTY_LENGTH'] = str(int(f.info.length))
            for tag in f.tags:
                if len(tag[1]) > 131072 or \
                        (tag[0] in tags and len(tags[tag[0]]) + len(tag[1]) > 131072):
                    mess = f'Tag "{tag[0]}" has value larger than csv field limit (131072) and will be skipped in file "{file_name}"'
                    click.echo('\n' + mess)
                    log.warning(mess)
                    continue
                if tag[0] in tags:  # adding same key with one more value
                    tags[tag[0]] += ';' + tag[1]
                else:
                    tags[tag[0]] = tag[1]
        except:
            click.echo(f"\nCant open file: {file_name}")
            return None

    if is_mp3(file_name):
        try:
            f = MP3(file_name, ID3=EasyID3)
            tags['SPOTY_LENGTH'] = str(int(f.info.length))
            f = EasyID3(file_name)
            for tag in f.valid_keys.keys():
                if tag in f:
                    tag_val = ';'.join(f[tag])
                    if len(tag_val) > 131072:
                        mess = f'Tag "{tag[0]}" has value larger than csv field limit (131072) and will be skipped in file "{file_name}"'
                        click.echo('\n' + mess)
                        log.warning(mess)
                        continue
                    tags[tag.upper()] = tag_val
        except:
            click.echo(f"\nCant open file: {file_name}")
            return None

    tags = spoty.utils.clean_tags_after_read(tags)

    return tags
