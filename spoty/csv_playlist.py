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


def create_csvs(tags, export_path, csvs_naming_pattern, overwrite):
    export_path = os.path.abspath(export_path)

    exported_csv_file_names = []
    exported_csv_names = []
    exported_tags = []

    if len(tags) > 0:
        grouped_tags = spoty.utils.group_tags_by_pattern(tags, csvs_naming_pattern)

        for group, tags in grouped_tags.items():
            csv_name = group
            csv_name = spoty.utils.slugify_file_pah(csv_name)
            csv_file_name = os.path.join(export_path, csv_name + '.csv')

            if csv_file_name in exported_csv_file_names:
                write_tags_to_csv(tags, csv_file_name, True)
            else:
                if os.path.isfile(csv_file_name) and not overwrite:
                    if not click.confirm(f'File "{csv_file_name}" already exist. Overwrite?'):
                        continue

                write_tags_to_csv(tags, csv_file_name, False)

            exported_csv_names.append(csv_name)
            exported_csv_file_names.append(csv_file_name)
            exported_tags.extend(tags)

    return exported_csv_file_names, exported_csv_names, exported_tags


def find_csvs_in_path(path, recursive=True):
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


def read_tags_from_csvs(csv_file_names, add_spoty_tags=True, filter_have_tags=None, filter_have_no_tags=None):
    all_tags_lists = []
    for csv_file_name in csv_file_names:
        tags_list = read_tags_from_csv(csv_file_names, add_spoty_tags, filter_have_tags, filter_have_no_tags)
        all_tags_lists.extend(tags_list)

    return all_tags_lists


def read_tags_from_csv(csv_file_name, add_spoty_tags=True, filter_have_tags=None, filter_have_no_tags=None):
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
            if len(row) == 0:
                continue

            tags = {}

            if (add_spoty_tags):
                tags['SPOTY_PLAYLIST_NAME'] = csv_file_name
                tags['SPOTY_PLAYLIST_INDEX'] = i - 1

            for h, key in enumerate(header):
                if len(row[h]) > 0:
                    tags[key] = row[h]

            if not spoty.utils.check_all_tags_exist(tags, filter_have_tags):
                continue

            if spoty.utils.check_all_tags_exist(tags, filter_have_no_tags):
                continue

            tags_list.append(tags)

    return tags_list


def create_csv_from_audio_files(csv_file_name, audio_file_names, overwrite=False):
    log.info(f'Exporting csv (tracks:{len(audio_file_names)}, file name: {csv_file_name})')

    if os.path.isfile(csv_file_name) and not overwrite:
        time.sleep(0.2)  # waiting progressbar updating
        if not click.confirm(f'\nFile "{csv_file_name}" already exist. Overwrite?'):
            log.info(f'Canceled by user (file already exist)')
            return None

    tags_list = spoty.audio_files.read_audio_files_tags(audio_file_names)

    write_tags_to_csv(tags_list, csv_file_name)

    return tags_list


def find_duplicates_in_csvs(path, compare_tags, recursive=True, filter_names=None):
    tags_list = []

    file_names = find_csvs_in_path(path, recursive, filter_names)
    for file_name in file_names:
        tags = read_tags_from_csv(file_name, True)
        tags_list.extend(tags)

    duplicates, skipped_tags = spoty.utils.find_duplicates_in_tags(tags_list, compare_tags)

    return duplicates, tags_list, skipped_tags
