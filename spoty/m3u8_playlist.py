from spoty import log
import spoty.utils
import spoty.audio_files
import click
import os
import time
import re


def is_m3u8(file_name):
    return file_name.upper().endswith('.M3U8')


def create_m3u8s(tags_list, path, grouping_pattern, overwrite=False, append=False, allow_duplicates=True,
                 confirm=False, compare_tags_list=None):
    path = os.path.abspath(path)

    if compare_tags_list is None:
        compare_tags_list = []

    all_created_m3u8_file_names = []
    all_created_m3u8_names = []
    all_added_tags = []
    all_import_duplicates = []
    all_already_exist = []

    if len(tags_list) > 0:
        grouped_tags = spoty.utils.group_tags_by_pattern(tags_list, grouping_pattern)

        for group, tags_l in grouped_tags.items():
            m3u8_name = spoty.utils.slugify_file_pah(group)
            m3u8_file_name = os.path.join(path, m3u8_name + '.m3u8')

            create_new_file = True
            if os.path.isfile(m3u8_file_name):
                if append:
                    create_new_file = False
                elif overwrite:
                    if not confirm:
                        if not click.confirm(f'File "{m3u8_file_name}" already exist. Overwrite?'):
                            click.echo("\nCanceled")
                            continue
                        click.echo("")  # for new line
                else:
                    m3u8_file_name = spoty.utils.find_empty_file_name(m3u8_file_name)

            if not allow_duplicates:
                for compare_tags_str in compare_tags_list:
                    compare_tags = compare_tags_str.split(',')
                    tags_l, import_duplicates = spoty.utils.remove_duplicated_tags(tags_l, compare_tags, False)
                    all_import_duplicates.extend(import_duplicates)

                if len(all_import_duplicates) > 0:
                    log.debug(f'{len(all_import_duplicates)} duplicates found when adding tracks. It will be skipped.')

                if not create_new_file:
                    exist_tags_list = read_tags_from_m3u8(m3u8_file_name)
                    for compare_tags_str in compare_tags_list:
                        compare_tags = compare_tags_str.split(',')
                        tags_l, exist_tags = spoty.utils.remove_exist_tags(exist_tags_list, tags_l, compare_tags, False)
                        all_already_exist.extend(exist_tags)

            write_tags_to_m3u8(tags_l, m3u8_file_name, not create_new_file)

            all_created_m3u8_names.append(m3u8_name)
            all_created_m3u8_file_names.append(m3u8_file_name)
            all_added_tags.extend(tags_l)

    return all_created_m3u8_file_names, all_created_m3u8_names, all_added_tags, all_import_duplicates, all_already_exist


def find_m3u8s_in_paths(paths, recursive=True):
    all_m3u8s = []

    for path in paths:
        file_names = find_m3u8s_in_path(path, recursive)
        all_m3u8s.extend(file_names)

    return all_m3u8s


def find_m3u8s_in_path(path, recursive=True):
    path = os.path.abspath(path)

    if not spoty.utils.is_valid_path(path):
        raise Exception("Path is not valid: " + path)

    full_file_names = []
    if recursive:
        full_file_names = [os.path.join(dp, f) for dp, dn, filenames in os.walk(path) for f in filenames if
                           is_m3u8(os.path.splitext(f)[1])]
    else:
        full_file_names = [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        full_file_names = list(filter(lambda f: is_m3u8(f), full_file_names))

    return full_file_names


def write_tags_to_m3u8(tags_list, m3u8_file_name, append=False):
    tags_list = spoty.utils.clean_tags_list_before_write(tags_list)

    if tags_list is None or len(tags_list) == 0:
        return

    if append:
        if os.path.isfile(m3u8_file_name):
            old_tags = read_tags_from_m3u8(m3u8_file_name, False)
            old_tags.extend(tags_list)
            tags_list = old_tags

    # collect all file_names
    files = []
    for tags in tags_list:
        if 'SPOTY_FILE_NAME' in tags and tags['SPOTY_FILE_NAME'] != "":
            files.append(tags['SPOTY_FILE_NAME'] + "\n")

    os.makedirs(os.path.dirname(m3u8_file_name), exist_ok=True)
    with open(m3u8_file_name, 'w', encoding='utf-8-sig', newline='') as file:
        file.writelines(files)


def read_tags_from_m3u8s(m3u8_file_names, add_spoty_tags=True, clean_tags=True):
    all_tags_lists = []
    for m3u8_file_name in m3u8_file_names:
        tags_list = read_tags_from_m3u8(m3u8_file_name, add_spoty_tags, clean_tags)
        all_tags_lists.extend(tags_list)

    return all_tags_lists


def read_tags_from_m3u8(m3u8_file_name, add_spoty_tags=True, clean_tags=True):
    m3u8_file_name = os.path.abspath(m3u8_file_name)

    with open(m3u8_file_name, newline='', encoding='utf-8-sig') as file:
        files_list = file.readlines()
        for i, f in enumerate(files_list):
            files_list[i] = f.rstrip("\n").strip()

    tags_list = spoty.audio_files.read_audio_files_tags(files_list, add_spoty_tags, clean_tags)

    if add_spoty_tags:
        for i, tags in enumerate(tags_list):
            tags['SPOTY_PLAYLIST_NAME'] = os.path.splitext(os.path.basename(os.path.normpath(m3u8_file_name)))[0]
            tags['SPOTY_PLAYLIST_INDEX'] = str(i + 1)

    return tags_list
