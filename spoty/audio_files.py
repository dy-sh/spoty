from spoty import log
import spoty.utils
import os.path
import click
import time
from mutagen.flac import FLAC


# from mutagen.mp3 import MP3
# from mutagen.id3 import ID3

def is_flac(file_name):
    return file_name.upper().endswith('.FLAC')


def is_mp3(file_name):
    return file_name.upper().endswith('.MP3')


def find_audio_files_in_paths(paths, recursive=True, filter_have_tags=None, filter_have_no_tags=None):
    all_file_names = []

    for path in paths:
        file_names = find_audio_files_in_path(path, recursive, filter_have_tags, filter_have_no_tags)
        all_file_names.extend(file_names)

    return all_file_names


def find_audio_files_in_path(path, recursive=True, filter_have_tags=None, filter_have_no_tags=None):
    path = os.path.abspath(path)
    file_names = []

    if recursive:
        file_names = [os.path.join(dp, f) for dp, dn, filenames in os.walk(path) for f in filenames if
                      is_flac(os.path.splitext(f)[1]) or is_mp3(os.path.splitext(f)[1])]
    else:
        file_names = [os.path.join(path, f) for f in os.listdir(path) if
                      os.path.isfile(os.path.join(path, f))]
        file_names = list(
            filter(lambda f: is_flac(f) or is_mp3(f), file_names))

    if len(filter_have_tags) > 0:
        file_names = filter_audio_files_which_have_all_tags(file_names, filter_have_tags)

    if len(filter_have_no_tags) > 0:
        file_names = filter_audio_files_which_not_have_any_of_tags(file_names, filter_have_no_tags)

    return file_names


def filter_audio_files_which_have_all_tags(file_names, tags):
    filtered = []
    for file_name in file_names:
        file_tags = read_audio_file_tags(file_name)
        if spoty.utils.check_all_tags_exist(file_tags, tags):
            filtered.append(file_name)
    return filtered


def filter_audio_files_which_not_have_any_of_tags(file_names, tags):
    filtered = []
    for file_name in file_names:
        file_tags = read_audio_file_tags(file_name)
        if not spoty.utils.check_all_tags_exist(file_tags, tags):
            filtered.append(file_name)
    return filtered


def write_audio_file_tags(file_name, new_tags):
    if len(new_tags) > 0:
        if is_flac(file_name):
            f = FLAC(file_name)
            for key, value in new_tags.items():
                f[key] = str(value)
            f.save()


def read_audio_files_tags(file_names, add_spoty_tags=True):
    tags_list = []
    for file_name in file_names:
        tags = read_audio_file_tags(file_name, add_spoty_tags)
        tags_list.append(tags)
    return tags_list


def read_audio_file_tags(file_name, add_spoty_tags=True):
    tags = {}

    file_name = os.path.abspath(file_name)

    if add_spoty_tags:
        dir = os.path.dirname(file_name)
        tags['SPOTY_FILE_NAME'] = file_name
        tags['SPOTY_PLAYLIST_SOURCE'] = "LOCAL"
        tags['SPOTY_PLAYLIST_NAME'] = os.path.basename(os.path.normpath(dir))

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
                    (tag[0] in tags and len(tags[tag[0]]) + len(tag[1]) > 131072):
                time.sleep(0.2)
                mess = f'Tag "{tag[0]}" has value larger than csv field limit (131072) and will be skipped in file "{file_name}"'
                click.echo('\n' + mess)
                log.warning(mess)
                continue
            if tag[0] in tags:
                tags[tag[0]] += ';' + tag[1]
            else:
                tags[tag[0]] = tag[1]

        tags['LENGTH'] = str(int(f.info.length * 1000))
    return tags


def get_missing_tags_in_audio_file(file_name, new_tags):
    exist_tags = read_audio_file_tags(file_name)
    missing_tags = spoty.utils.get_missing_tags(exist_tags, new_tags)
    return missing_tags


def get_missing_tags_from_source_to_dest_audio_files(source_tags, dest_tags, compare_tags):
    missing_tags = {}
    with click.progressbar(source_tags, label='Searching missing tags in files') as bar:
        for src_tags in bar:
            for dest_tags in dest_tags:
                if spoty.utils.compare_tags(src_tags, dest_tags, compare_tags):
                    dest_file_name = dest_tags['SPOTY_FILE_NAME']
                    tags = get_missing_tags_in_audio_file(dest_file_name, src_tags)
                    if len(tags) > 0:
                        missing_tags[dest_file_name] = tags
    return missing_tags


def write_missing_tags_to_audio_files(source_tags_list, dest_tags_list, compare_tags):
    edited_files = []
    with click.progressbar(source_tags_list, label='Writing missing tags to files') as bar:
        for src_tags in bar:
            for dest_tags_list in dest_tags_list:
                if spoty.utils.compare_tags(src_tags, dest_tags_list, compare_tags):
                    file_name = dest_tags_list['SPOTY_FILE_NAME']
                    missing_tags = get_missing_tags_in_audio_file(file_name, src_tags)
                    if len(missing_tags) > 0:
                        write_audio_file_tags(file_name, missing_tags)
                        edited_files.append(file_name)
                        # click.echo(f'Added {str(added_tags)} to {file_name}')
                        # log.debug(f'Added {str(added_tags)} to {file_name}')
    return edited_files, dest_tags_list


def fix_invalid_audio_file_tags(path, recursive=True, filter_have_tags=None, filter_have_no_tags=None):
    file_names = find_audio_files_in_paths(path, recursive)
    tags_list = read_audio_files_tags(file_names)

    edited_files = []

    # replace ',' to ';' in ARTIST tag
    replace_comma = []
    for tags in tags_list:
        if ',' in tags['ARTIST']:
            replace_comma.append(tags)
    if len(replace_comma) > 0:
        for tags in replace_comma:
            file_name = tags['SPOTY_FILE_NAME']
            click.echo(f'ARTIST: "{tags["ARTIST"]}" in "{file_name}"')
        click.echo(f'Total audio files: {len(replace_comma)}')
        if (click.confirm("Do you want to replace ',' to ';' in this audio files?")):
            for tags in replace_comma:
                file_name = tags['SPOTY_FILE_NAME']
                f = FLAC(file_name)
                artists = f.tags['ARTIST']
                for i in range(len(artists)):
                    artists[i] = artists[i].replace(',', ';')
                f['ARTIST'] = artists
                f.save()
                if tags not in edited_files:
                    edited_files.append(tags)

    return edited_files, file_names


def find_duplicates_in_audio_files(path, compare_tags, recursive=True, filter_have_tags=None, filter_have_no_tags=None):
    if len(compare_tags) == 0:
        return

    file_names = find_audio_files_in_path(path, recursive, filter_have_tags, filter_have_no_tags)
    tags_list = read_audio_files_tags(file_names)
    duplicates, skipped_audio_files = spoty.utils.find_duplicates_in_tags(tags_list, compare_tags)

    return duplicates, tags_list, skipped_audio_files
