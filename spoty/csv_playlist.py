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


def create_csvs(tags_list, path, grouping_pattern, overwrite=False, append=False, remove_duplicates=False,
                confirm=False, compare_tags_list=None):
    path = os.path.abspath(path)

    if compare_tags_list is None:
        compare_tags_list = []

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

            if remove_duplicates:
                for compare_tags_str in compare_tags_list:
                    compare_tags = compare_tags_str.split(',')
                    tags_l, import_duplicates = spoty.utils.remove_duplicated_tags(tags_l, compare_tags, False)
                    all_import_duplicates.extend(import_duplicates)

                if len(all_import_duplicates) > 0:
                    log.debug(f'{len(all_import_duplicates)} duplicates found when adding tracks. It will be skipped.')

                if not create_new_file:
                    exist_tags_list = read_tags_from_csv(csv_file_name)
                    for compare_tags_str in compare_tags_list:
                        compare_tags = compare_tags_str.split(',')
                        tags_l, exist_tags = spoty.utils.remove_exist_tags(exist_tags_list, tags_l, compare_tags, False)
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
    tags_list = spoty.utils.clean_tags_list_before_write(tags_list)

    for i, tags in enumerate(tags_list):
        for key, value in tags.items():
            if type(value) is str:
                if len(value) > 131072:
                    mess = f'Tag "{key}" has value larger than csv field limit (131072) and will be truncated (file: "{csv_file_name}", line: {i + 1}).'
                    click.echo('\n' + mess)
                    log.warning(mess)
                    tags[key] = value[0: 131071]

    if tags_list is None or len(tags_list) == 0:
        return

    if append:
        if os.path.isfile(csv_file_name):
            old_tags = read_tags_from_csv(csv_file_name, False, False)
            old_tags.extend(tags_list)
            tags_list = old_tags

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

    rows = []
    rows.append(keys)  # header
    for tags in tags_list:
        row = [tags[key] for key in keys]
        rows.append(row)

    os.makedirs(os.path.dirname(csv_file_name), exist_ok=True)
    with open(csv_file_name, 'w', encoding='utf-8-sig', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(rows)


def read_tags_from_csvs(csv_file_names, add_spoty_tags=True):
    all_tags_lists = []
    for csv_file_name in csv_file_names:
        tags_list = read_tags_from_csv(csv_file_name, add_spoty_tags)
        all_tags_lists.extend(tags_list)

    return all_tags_lists


def read_tags_from_csv(csv_file_name, add_spoty_tags=True, add_missing_tags=True):
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

            if all(item == "" for item in row):  # skip empty lines
                continue

            tags = {}

            for h, key in enumerate(header):
                if len(row[h]) > 0:
                    tags[key] = row[h]

            if add_spoty_tags:
                playlist_name = os.path.basename(csv_file_name)
                if playlist_name.upper().endswith('.CSV'):
                    playlist_name = playlist_name[:-4]
                tags['SPOTY_SOURCE'] = 'CSV'
                tags['SPOTY_PLAYLIST_NAME'] = playlist_name
                tags['SPOTY_PLAYLIST_INDEX'] = str(i)

            if add_missing_tags:
                tags = spoty.utils.clean_tags_after_read(tags)

            tags_list.append(tags)

    return tags_list
