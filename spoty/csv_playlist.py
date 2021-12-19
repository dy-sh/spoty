from spoty import log
import spoty.utils
import spoty.audio_files
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


def create_csvs(tags_list, path, grouping_pattern, overwrite=False, append=False, allow_duplicates=True,
                confirm=False, compare_duplicates_tags=None):
    path = os.path.abspath(path)

    if compare_duplicates_tags is None:
        compare_duplicates_tags = []

    all_created_csv_file_names = []
    all_created_csv_names = []
    all_added_tags = []
    all_import_duplicates = []
    all_already_exist = []

    if len(tags_list) > 0:
        grouped_tags = spoty.utils.group_tags_by_pattern(tags_list, grouping_pattern)

        for group, tags_l in grouped_tags.items():
            csv_name = spoty.utils.slugify_file_pah(group)
            csv_file_name = os.path.join(path, csv_name + '.csv')

            create_new_file = True
            if os.path.isfile(csv_file_name):
                if append:
                    create_new_file = False
                elif overwrite:
                    if not confirm:
                        if not click.confirm(f'File "{csv_file_name}" already exist. Overwrite?'):
                            click.echo("\nCanceled")
                            continue
                        click.echo("")  # for new line
                else:
                    csv_file_name = spoty.utils.find_empty_file_name(csv_file_name)


            if not allow_duplicates:
                tags_l, import_duplicates = spoty.utils.remove_tags_duplicates(tags_l, compare_duplicates_tags)
                if len(import_duplicates) > 0:
                    log.debug(f'{len(import_duplicates)} duplicates found when adding tracks. It will be skipped.')
                if not create_new_file:
                    exist_tags_list = read_tags_from_csv(csv_file_name)
                    tags_l, exist_tags = spoty.utils.remove_exist_tags(exist_tags_list, tags_l, compare_duplicates_tags)
                    all_already_exist.extend(exist_tags)

            write_tags_to_csv(tags_l, csv_file_name, not create_new_file)

            all_created_csv_names.append(csv_name)
            all_created_csv_file_names.append(csv_file_name)
            all_added_tags.extend(tags_l)

    return all_created_csv_file_names, all_created_csv_names, all_added_tags, all_import_duplicates, all_already_exist


def find_csvs_in_paths(paths, recursive=True):
    all_csvs = []

    for path in paths:
        file_names = find_csvs_in_path(path, recursive)
        all_csvs.extend(file_names)

    return all_csvs


def find_csvs_in_path(path, recursive=True):
    path = os.path.abspath(path)

    if not spoty.utils.is_valid_path(path):
        raise Exception("Path is not valid: " + path)

    full_file_names = []
    if recursive:
        full_file_names = [os.path.join(dp, f) for dp, dn, filenames in os.walk(path) for f in filenames if
                           is_csv(os.path.splitext(f)[1])]
    else:
        full_file_names = [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        full_file_names = list(filter(lambda f: is_csv(f), full_file_names))

    return full_file_names


def write_tags_to_csv(tags_list, csv_file_name, append=False):
    # collect all keys
    keys = []
    for tags in tags_list:
        for key, value in tags.items():
            if not key in keys:
                keys.append(key)

    keys = spoty.utils.reorder_tag_keys_main_first(keys)

    # add missing keys
    for tags in tags_list:
        for key in keys:
            if not key in tags:
                tags[key] = ""

    os.makedirs(os.path.dirname(csv_file_name), exist_ok=True)

    method = 'w'
    if append:
        if os.path.isfile(csv_file_name):
            with open(csv_file_name, newline='', encoding='utf-8-sig') as file:
                reader = csv.reader(file)
                if sum(1 for row in reader) != 0:  # file is not empty
                    method = 'a'

    with open(csv_file_name, method, encoding='utf-8-sig', newline='') as file:
        writer = csv.writer(file)

        if method == 'w':  # write header to new file
            writer.writerow(keys)

        for tags in tags_list:
            values = [tags[key] for key in keys]
            writer.writerow(values)


def read_tags_from_csvs(csv_file_names, filter_have_tags=None, filter_have_no_tags=None, add_spoty_tags=True):
    all_tags_lists = []
    for csv_file_name in csv_file_names:
        tags_list = read_tags_from_csv(csv_file_name, filter_have_tags, filter_have_no_tags, add_spoty_tags)
        all_tags_lists.extend(tags_list)

    return all_tags_lists


def read_tags_from_csv(csv_file_name, filter_have_tags=None, filter_have_no_tags=None, add_spoty_tags=True):
    csv_file_name = os.path.abspath(csv_file_name)
    tags_list = []

    with open(csv_file_name, newline='', encoding='utf-8-sig') as file:
        reader = csv.reader(file)
        if sum(1 for row in reader) == 0:
            raise CSVFileEmpty()

    with open(csv_file_name, newline='', encoding='utf-8-sig') as file:
        header = []
        reader = csv.reader(file)

        for i, row in enumerate(reader):
            # read header

            if (i == 0):
                header = row
                if len(header) == 0:
                    raise CSVFileInvalidHeader()
                continue

            # read tags

            if len(row) == 0:  # skip empty lines
                continue

            tags = {}

            for h, key in enumerate(header):
                if len(row[h]) > 0:
                    tags[key] = row[h]

            if len(filter_have_tags) > 0:
                if not spoty.utils.check_all_tags_exist(tags, filter_have_tags):
                    continue

            if len(filter_have_no_tags) > 0:
                if spoty.utils.check_all_tags_exist(tags, filter_have_no_tags):
                    continue

            if (add_spoty_tags):
                playlist_name = os.path.basename(csv_file_name)
                if playlist_name.upper().endswith('.CSV'):
                    playlist_name = playlist_name[:-4]
                tags['SPOTY_PLAYLIST_SOURCE'] = 'CSV'
                tags['SPOTY_PLAYLIST_NAME'] = playlist_name
                tags['SPOTY_PLAYLIST_INDEX'] = i

            tags_list.append(tags)

    return tags_list


def create_csv_from_audio_files(csv_file_name, audio_file_names, overwrite=False):
    log.info(f'Exporting csv (tracks:{len(audio_file_names)}, file name: {csv_file_name})')

    if os.path.isfile(csv_file_name) and not overwrite:
        time.sleep(0.2)  # waiting progressbar updating
        if not click.confirm(f'\nFile "{csv_file_name}" already exist. Overwrite?'):
            click.echo("\nCanceled")
            log.info(f'Canceled by user (file already exist)')
            return None
        click.echo("")  # for new line

    tags_list = spoty.audio_files.read_audio_files_tags(audio_file_names)

    write_tags_to_csv(tags_list, csv_file_name)

    return tags_list


def find_duplicates_in_csvs(path, compare_tags, recursive=True, filter_names=None):
    tags_list = []

    file_names = find_csvs_in_path(path, recursive, filter_names)
    for file_name in file_names:
        tags = read_tags_from_csv(file_name)
        tags_list.extend(tags)

    duplicates, skipped_tags = spoty.utils.find_duplicates_in_tags(tags_list, compare_tags)

    return duplicates, tags_list, skipped_tags
