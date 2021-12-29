import os.path
from datetime import datetime
import click
from spoty import settings
from typing import List
import dateutil.parser
import numpy as np
from multiprocessing import Process, Lock, Queue, Value, Array
import sys
import time

THREADS_COUNT = 12

tag_allies = [
    ['YEAR', 'DATE'],
    ['TRACK', 'TRACKNUMBER'],
    ['DISK', 'DISKNUMBER']
]

spoty_tags = \
    [
        'SPOTY_DUP_GROUP',
        'SPOTY_DEF_DUP_TAGS',
        'SPOTY_PROB_DUP_TAGS',
        'SPOTY_DUP_LIST',
        'SPOTY_DUP_ID',
        'SPOTY_FOUND_BY',
        'SPOTY_SOURCE',
        'SPOTY_PLAYLIST_NAME',
        'SPOTY_PLAYLIST_ID',
        'SPOTY_PLAYLIST_INDEX',
        'SPOTY_FILE_NAME',
        'SPOTY_TRACK_ID',
        'SPOTY_TRACK_ADDED',
        'SPOTY_LENGTH',
    ]

spotify_tags = [
    'SPOTIFY_TRACK_ID',
    'SPOTIFY_ALBUM_ID',
]

deezer_tags = [
    'DEEZER_TRACK_ID',
    'DEEZER_ALBUM_ID',
    'DEEZER_ARTIST_ID',
    'DEEZER_LYRICS_ID',
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
        'SOURCE'
        'BPM',
        'QUALITY',
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
        'EXPLICIT',
        'FILEOWNER',
        'GAIN',
        'INITIAL KEY',
        'INITIALKEY',
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
        'RELEASE DATE',
        'STYLE',
        'TOTALDISCS',
        'TOTALTRACKS',
        'TRACK',
        'UPC',
        'WRITER',
    ]


class DuplicatesGroup:
    source_tags: dict
    def_duplicates: list
    prob_duplicates: list
    def_found_tags: list
    prob_found_tags: list

    def __init__(self):
        self.source_tags = {}
        self.def_duplicates = []
        self.prob_duplicates = []
        self.def_found_tags = []
        self.prob_found_tags = []

    def get_duplicates_count(self):
        return len(self.def_duplicates) + len(self.prob_duplicates)

    def has_duplicates(self):
        return self.get_duplicates_count() > 0


class SpotyContext:
    tags_lists: list
    summary: list
    duplicates_groups: List[DuplicatesGroup]
    unique_first_tracks: list
    unique_second_tracks: list

    def __init__(self):
        self.tags_lists = []
        self.summary = []
        self.duplicates_groups = []
        self.unique_first_tracks = []
        self.unique_second_tracks = []


mutex = Lock()


def tuple_to_list(some_tuple: tuple):
    l = []
    l.extend(some_tuple)
    return l


def dict_to_list(some_dics: dict):
    l = []
    for key, value in some_dics.items():
        l.append(value)
    return l


def is_valid_path(path: str):
    return os.path.isdir(path)


def is_valid_file(path: str):
    return os.path.isfile(path)


def slugify_file_pah(text: str):
    # valid_chars = "-_.()=!@#$%%^&+ %s%s" % (string.ascii_letters, string.digits)
    # return ''.join(c for c in text if c in valid_chars).strip()

    valid_chars = '<>:"/\|?*'

    for char in valid_chars:
        text = text.replace(char, '')

    return text


def filter_duplicates(src_arr: list, dest_arr: list):
    return list(filter(lambda id: id not in src_arr, dest_arr))


def remove_duplicates(arr: list):
    good = []
    duplicates = []
    for item in arr:
        if item in good:
            duplicates.append(item)
        else:
            good.append(item)
    return good, duplicates


def remove_exist(exist_arr: list, new_arr: list):
    new = []
    exist = []
    for item in new_arr:
        if item in exist_arr:
            exist.append(item)
        else:
            new.append(item)
    return new, exist


def remove_duplicated_tags(tags_list: list, tags_to_compare: list, allow_missing=False):
    good = []
    duplicates = []
    for new_tags in tags_list:
        found = False
        for exist_tags in good:
            if compare_tags(exist_tags, new_tags, tags_to_compare, allow_missing):
                duplicates.append(new_tags)
                found = True
                break
        if not found:
            good.append(new_tags)

    return good, duplicates


def remove_exist_tags(exist_tags_list: list, new_tags_list: list, tags_to_compare: list, allow_missing=False):
    new = []
    exist = []
    for new_tags in new_tags_list:
        found = False
        for exist_tags in exist_tags_list:
            if compare_tags(exist_tags, new_tags, tags_to_compare, allow_missing):
                exist.append(new_tags)
                found = True
                break
        if not found:
            new.append(new_tags)

    return new, exist


def compare_tags(tags1: dict, tags2: dict, tags_to_compare: list, allow_missing=False):
    for tag in tags_to_compare:

        if not tag in tags1 or not tag in tags2:
            if allow_missing:
                continue
            else:
                return False

        if tag == 'SPOTY_LENGTH':
            if abs(int(tags1['SPOTY_LENGTH']) - int(
                    tags2['SPOTY_LENGTH'])) > settings.SPOTY.COMPARE_LENGTH_TOLERANCE_SEC:
                return False
            else:
                continue

        if tag == "ARTIST":
            artist1 = tags1[tag].replace(',', ';').upper()
            artist1 = artist1.split(';')
            artist2 = tags2[tag].replace(',', ';').upper()
            artist2 = artist2.split(';')
            found = False
            for art in artist1:
                if art in artist2:
                    found = True
            if not found:
                return False
            else:
                continue

        if tag == "TITLE":
            title1 = tags1[tag].upper()
            title1 = ''.join(char for char in title1 if char.isalnum())
            title2 = tags2[tag].upper()
            title2 = ''.join(char for char in title2 if char.isalnum())
            if not title2.startswith(title1) and not title1.startswith(title2):
                return False
            else:
                continue

        if tag == "ALBUM":
            album1 = tags1[tag].upper()
            album2 = tags2[tag].upper()
            if not album2.startswith(album1) and not album1.startswith(album2):
                return False
            else:
                continue

        if tags1[tag] != tags2[tag]:
            return False

    return True


def find_duplicates_in_tags(tags_list: list, compare_tags: list):
    if len(compare_tags) == 0:
        return

    duplicates = {}
    pattern = ""
    for tag in compare_tags:
        pattern += "%" + tag + "%,"
    pattern = pattern[:-1]

    groupped_tags = group_tags_by_pattern(tags_list, pattern, "Unknown")

    for group, tags in groupped_tags.items():
        if group == "Unknown":
            continue
        if len(tags) > 1:
            if not group in duplicates:
                duplicates[group] = []
            duplicates[group].extend(tags)

    skipped_tags = groupped_tags['Unknown'] if 'Unknown' in groupped_tags else []

    return duplicates, skipped_tags


def print_main_tags(tags: dict):
    if 'ISRC' in tags: print(f'ISRC: {tags["ISRC"]}')
    if 'ARTIST' in tags: print(f'ARTIST: {tags["ARTIST"]}')
    if 'TITLE' in tags: print(f'TITLE: {tags["TITLE"]}')
    if 'ALBUM' in tags: print(f'ALBUM: {tags["ALBUM"]}')
    if 'GENRE' in tags: print(f'GENRE: {tags["GENRE"]}')
    if 'MOOD' in tags: print(f'MOOD: {tags["MOOD"]}')
    if 'OCCASION' in tags: print(f'OCCASION: {tags["OCCASION"]}')
    if 'RATING' in tags: print(f'RATING: {tags["RATING"]}')
    if 'COMMENT' in tags: print(f'COMMENT: {tags["COMMENT"]}')
    if 'BARCODE' in tags: print(f'BARCODE: {tags["BARCODE"]}')
    if 'SPOTY_LENGTH' in tags: print(f'SPOTY_LENGTH: {tags["SPOTY_LENGTH"]}')
    if 'SPOTIFY_TRACK_ID' in tags: print(f'SPOTIFY_TRACK_ID: {tags["SPOTIFY_TRACK_ID"]}')
    if 'SOURCE' in tags: print(f'SOURCE: {tags["SOURCE"]}')
    if 'SOURCEID' in tags: print(f'SOURCEID: {tags["SOURCEID"]}')
    if 'YEAR' in tags: print(f'YEAR: {tags["YEAR"]}')


def print_tags_list_grouped(tags_list: list, print_pattern: str, grouping_pattern: str):
    if len(tags_list) == 0:
        return

    grouped_tags = group_tags_by_pattern(tags_list, grouping_pattern)

    for group, tags_l in grouped_tags.items():
        print(f'\n------------------------- {group}:')
        print_tags_list(tags_list, print_pattern)


def print_tags_list(tags_list: list, print_pattern: str):
    if len(tags_list) == 0:
        return

    for tags in tags_list:
        txt = parse_pattern(tags, print_pattern)
        print("  " + txt)


def print_duplicates_tags_list(tags_list: list, print_pattern: str = None):
    if len(tags_list) == 0:
        return

    for tags in tags_list:
        if print_pattern is None:
            print_pattern = settings.DUPLICATE_PRINT_PATTERN[tags['SPOTY_SOURCE']]
        txt = parse_pattern(tags, print_pattern)
        print("  " + txt)


def check_tag_has_allies(tag: str):
    for allies in tag_allies:
        if tag in allies:
            return True
    return False


def get_tag_allies(tag: str, include_source_tag=True):
    res = []
    for allies in tag_allies:
        if tag in allies:
            res = allies.copy()

    if tag in res:
        res.remove(tag)

    if include_source_tag:
        res.append(tag)
    return res


def print_tags(tags: dict, tags_to_print: list):
    for tag in tags_to_print:
        allies = get_tag_allies(tag, True)
        for a in allies:
            if a.upper() in tags:
                print(f'{a}: {tags[a]}')


def add_playlist_index_from_playlist_names(tags_list: list):
    res = []
    groups = group_tags_by_pattern(tags_list, "%SPOTY_PLAYLIST_NAME%")
    for group, g_tags_list in groups.items():
        for i, tags in enumerate(g_tags_list):
            tags['SPOTY_PLAYLIST_INDEX'] = str(i + 1)
            res.append(tags)
    return res


def filter_tags_list_have_tags(tags_list: list, filter_tags: list):
    filtered = []
    for tags in tags_list:
        if check_all_tags_exist(tags, filter_tags):
            filtered.append(tags)
    return filtered


def filter_tags_list_have_no_tags(tags_list: list, filter_tags: list):
    filtered = []
    for tags in tags_list:
        if not check_all_tags_exist(tags, filter_tags):
            filtered.append(tags)
    return filtered


def filter_added_after_date(tags_list: list, date: str, add_if_date_tag_missing=False):
    filtered = []
    for tags in tags_list:
        if 'SPOTY_TRACK_ADDED' in tags:
            track_added = datetime.strptime(tags['SPOTY_TRACK_ADDED'], "%Y-%m-%d %H:%M:%S")
            # specified_date = datetime.strptime(added_after_time, "%Y-%m-%d %H:%M:%S")
            try:
                specified_date = dateutil.parser.parse(date)
            except:
                click.echo(f'Cant parse date: "{date}". Use this format: "2018-06-29 08:15:27"', err=True)
                exit()
            if track_added > specified_date:
                filtered.append(tags)
        else:
            if add_if_date_tag_missing:
                filtered.append(tags)
    return filtered


def filter_added_before_date(tags_list: list, date: str, add_if_date_tag_missing=False):
    filtered = []
    for tags in tags_list:
        if 'SPOTY_TRACK_ADDED' in tags:
            track_added = datetime.strptime(tags['SPOTY_TRACK_ADDED'], "%Y-%m-%d %H:%M:%S")
            # specified_date = datetime.strptime(added_after_time, "%Y-%m-%d %H:%M:%S")
            try:
                specified_date = dateutil.parser.parse(date)
            except:
                click.echo(f'Cant parse date: "{date}". Use this format: "2018-06-29 08:15:27"', err=True)
                exit()
            if track_added < specified_date:
                filtered.append(tags)
        else:
            if add_if_date_tag_missing:
                filtered.append(tags)
    return filtered


def check_all_tags_exist(tags: dict, tags_to_check: list):
    for tag in tags_to_check:
        if not tag.upper() in tags:
            return False
    return True


def group_tags_by_pattern(tags_list: list, pattern: str, not_found_tag_name="Unknown"):
    groups = {}

    for tags in tags_list:
        group_name = parse_pattern(tags, pattern)

        if not group_name in groups:
            groups[group_name] = []

        groups[group_name].append(tags)

    return groups


def parse_pattern(tags: dict, pattern: str):
    result = ""
    tag_name = ""
    building_tag = False
    for c in pattern:
        if c == "%":
            building_tag = not building_tag
            if not building_tag:
                allies = get_tag_allies(tag_name, True)
                for a in allies:
                    if a in tags:
                        tag = tags[a]
                        result += str(tag)
                tag_name = ""
        else:
            if building_tag:
                tag_name += c
                tag_name = tag_name.upper()
            else:
                result += c

    return result


def reorder_tag_keys_main_first(keys: list):
    res = []

    # reorder spoty tags first
    for key in spoty_tags:
        if key in keys:
            res.append(key)

    for key in spotify_tags:
        if key in keys:
            res.append(key)

    for key in deezer_tags:
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


def get_missing_tags(exist_tags: dict, new_tags: dict):
    missing_tags = {}

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


def find_empty_file_name(exist_file_name: str):
    exist_file_name = os.path.abspath(exist_file_name)

    if not os.path.isfile(exist_file_name):
        return exist_file_name

    base_name = os.path.basename(exist_file_name)
    ext = os.path.splitext(base_name)[1]
    base_name = os.path.splitext(base_name)[0]
    dir_name = os.path.dirname(exist_file_name)
    i = 1
    while True:
        i += 1
        new_file_name = os.path.join(dir_name, base_name + f' {i}' + ext)
        if not os.path.isfile(new_file_name):
            return new_file_name


def clean_tags_list_before_write(tags_list):
    for tags in tags_list:
        if 'SPOTY_PLAYLIST_INDEX' in tags:
            del tags['SPOTY_PLAYLIST_INDEX']
        if 'LENGTH' in tags:
            del tags['LENGTH']
    return tags_list


def clean_tags_list_after_read(tags_list):
    for i, tags in enumerate(tags_list):
        tags_list[i] = clean_tags_after_read(tags)


def clean_tags_after_read(tags):
    # local files from deemix

    if 'SOURCEID' in tags and 'DEEZER_TRACK_ID' not in tags \
            and 'SOURCE' in tags and tags['SOURCE'].upper() == "DEEZER":
        tags['DEEZER_TRACK_ID'] = tags['SOURCEID']

    # missing deezer track id

    if 'SPOTY_SOURCE' in tags and tags['SPOTY_SOURCE'].upper() == "DEEZER":

        if 'SPOTY_TRACK_ID' not in tags and 'DEEZER_TRACK_ID' in tags:
            tags['SPOTY_TRACK_ID'] = tags['DEEZER_TRACK_ID']

        if 'DEEZER_TRACK_ID' not in tags and 'SPOTY_TRACK_ID' in tags:
            tags['DEEZER_TRACK_ID'] = tags['SPOTY_TRACK_ID']

    # missing spotify track id

    if 'SPOTY_SOURCE' in tags and tags['SPOTY_SOURCE'].upper() == "SPOTIFY":

        if 'SPOTY_TRACK_ID' not in tags and 'SPOTIFY_TRACK_ID' in tags:
            tags['SPOTY_TRACK_ID'] = tags['SPOTIFY_TRACK_ID']

        if 'SPOTIFY_TRACK_ID' not in tags and 'SPOTY_TRACK_ID' in tags:
            tags['SPOTIFY_TRACK_ID'] = tags['SPOTY_TRACK_ID']

    return tags


def find_duplicates_in_groups(check_tags: dict, groups: List[DuplicatesGroup], compare_tags_list: list,
                              compare_with_def_duplicates=False, compare_with_prob_duplicates=False) -> (
        DuplicatesGroup, list):
    if len(compare_tags_list) == 0:
        return None, None

    for tags_to_compare in compare_tags_list:
        for group in groups:
            if len(group.source_tags.items()) > 0:
                if compare_tags(check_tags, group.source_tags, tags_to_compare, False):
                    return group, tags_to_compare

    if compare_with_def_duplicates:
        for tags_to_compare in compare_tags_list:
            for group in groups:
                for tags in group.def_duplicates:
                    if compare_tags(check_tags, tags, tags_to_compare, False):
                        return group, tags_to_compare

    if compare_with_prob_duplicates:
        for tags_to_compare in compare_tags_list:
            for group in groups:
                for tags in group.prob_duplicates:
                    if compare_tags(check_tags, tags, tags_to_compare, False):
                        return group, tags_to_compare
    return None, None


def find_duplicates_in_tag_list2(tags_list: list, compare_tags_def_list: list, compare_tags_prob_list: list,
                                 add_dup_tags=False):
    # get tags to compare from config

    for i, tags in enumerate(compare_tags_def_list):
        compare_tags_def_list[i] = tags.split(',')

    for i, tags in enumerate(compare_tags_prob_list):
        compare_tags_prob_list[i] = tags.split(',')

    groups: List[DuplicatesGroup] = []

    # find duplicates

    with click.progressbar(tags_list, label=f'Finding duplicates in {len(tags_list)} tracks') as bar:
        for tags in bar:
            group, found_tags = find_duplicates_in_groups(tags, groups, compare_tags_def_list, True, True)
            if group is not None:
                group.def_duplicates.append(tags)
                group.def_found_tags.append(found_tags)
            else:
                group, found_tags = find_duplicates_in_groups(tags, groups, compare_tags_prob_list, True, True)
                if group is not None:
                    group.prob_duplicates.append(tags)
                    group.prob_found_tags.append(found_tags)
                else:
                    d = DuplicatesGroup()
                    d.source_tags = tags
                    groups.append(d)

    # remove unique

    unique_tracks = []
    duplicates_groups: List[DuplicatesGroup] = []
    for group in groups:
        if group.has_duplicates():
            duplicates_groups.append(group)
        else:
            unique_tracks.append(group.source_tags)

    if add_dup_tags:
        for i, group in enumerate(duplicates_groups):
            if len(group.source_tags.items()) > 0:
                group.source_tags['SPOTY_DUP_GROUP'] = i + 1
            for y, tags in enumerate(group.def_duplicates):
                tags['SPOTY_DUP_GROUP'] = i + 1
                tags['SPOTY_DEF_DUP_TAGS'] = ','.join(group.def_found_tags[y])
            for y, tags in enumerate(group.prob_duplicates):
                tags['SPOTY_DUP_GROUP'] = i + 1
                tags['SPOTY_PROB_DUP_TAGS'] = ','.join(group.prob_found_tags[y])

    return duplicates_groups, unique_tracks


def find_duplicates_in_tag_lists(source_list: list, dest_list: list, compare_tags_def_list: list,
                                 compare_tags_prob_list: list,
                                 add_dup_tags=False):
    # get tags to compare from config

    for i, tags in enumerate(compare_tags_def_list):
        compare_tags_def_list[i] = tags.split(',')

    for i, tags in enumerate(compare_tags_prob_list):
        compare_tags_prob_list[i] = tags.split(',')

    # find duplicates in dest

    groups: List[DuplicatesGroup] = []
    unique_dest_tracks = []

    for source_tags in source_list:
        d = DuplicatesGroup()
        d.source_tags = source_tags
        groups.append(d)

    if len(source_list) + len(dest_list) < 2000:  # single thread
        with click.progressbar(dest_list,
                               label=f'Finding duplicates in {len(source_list) + len(dest_list)} tracks') as bar:
            for dest_tags in bar:
                group, found_tags = find_duplicates_in_groups(dest_tags, groups, compare_tags_def_list)
                if group is not None:
                    group.def_duplicates.append(dest_tags)
                    group.def_found_tags.append(found_tags)
                else:
                    group, found_tags = find_duplicates_in_groups(dest_tags, groups, compare_tags_prob_list)
                    if group is not None:
                        group.prob_duplicates.append(dest_tags)
                        group.prob_found_tags.append(found_tags)
                    else:
                        unique_dest_tracks.append(dest_tags)
    else:  # multi thread
        try:
            parts = np.array_split(dest_list, THREADS_COUNT)
            threads = []
            counters = []
            results = Queue()

            with click.progressbar(length=len(dest_list),
                                   label=f'Finding duplicates in {len(source_list) + len(dest_list)} tracks') as bar:

                for i, part in enumerate(parts):
                    counter = Value('i', 0)
                    counters.append(counter)
                    dest_list_part = list(part)
                    thread = Process(target=find_duplicates_in_groups_thread, args=(
                        dest_list_part, groups, compare_tags_def_list, compare_tags_prob_list, counter, results))
                    threads.append(thread)
                    thread.daemon = True  # This thread dies when main thread exits
                    thread.start()

                    # update bar
                    total = sum([x.value for x in counters])
                    added = total - bar.pos
                    if added > 0:
                        bar.update(added)

                while not bar.finished:
                    time.sleep(0.1)
                    total = sum([x.value for x in counters])
                    added = total - bar.pos
                    if added > 0:
                        bar.update(added)

                for i in range(len(parts)):
                    res = results.get()
                    unique_dest_tracks.extend(res['unique_dest_tracks'])
                    for i, group in enumerate(res['groups']):
                        if len(group.def_duplicates) > 0:
                            groups[i].def_duplicates.extend(group.def_duplicates)
                            groups[i].def_found_tags.extend(group.def_found_tags)
                        if len(group.prob_duplicates) > 0:
                            groups[i].prob_duplicates.extend(group.prob_duplicates)
                            groups[i].prob_found_tags.extend(group.prob_found_tags)

        except (KeyboardInterrupt, SystemExit):  # aborted by user
            click.echo()
            click.echo('Aborted.')
            sys.exit()

    # remove unique source

    unique_source_tracks = []
    duplicates_groups: List[DuplicatesGroup] = []
    for group in groups:
        if group.has_duplicates():
            duplicates_groups.append(group)
        else:
            unique_source_tracks.append(group.source_tags)

    if add_dup_tags:
        for i, group in enumerate(duplicates_groups):
            group.source_tags['SPOTY_DUP_GROUP'] = i + 1
            for y, tags in enumerate(group.def_duplicates):
                tags['SPOTY_DUP_GROUP'] = i + 1
                tags['SPOTY_DEF_DUP_TAGS'] = ','.join(group.def_found_tags[y])
            for y, tags in enumerate(group.prob_duplicates):
                tags['SPOTY_DUP_GROUP'] = i + 1
                tags['SPOTY_PROB_DUP_TAGS'] = ','.join(group.prob_found_tags[y])

    return duplicates_groups, unique_source_tracks, unique_dest_tracks


def find_duplicates_in_groups_thread(dest_list, groups, compare_tags_def_list, compare_tags_prob_list, counter, result):
    unique_dest_tracks = []

    for i, dest_tags in enumerate(dest_list):
        group, found_tags = find_duplicates_in_groups(dest_tags, groups, compare_tags_def_list)
        if group is not None:
            group.def_duplicates.append(dest_tags)
            group.def_found_tags.append(found_tags)
        else:
            group, found_tags = find_duplicates_in_groups(dest_tags, groups, compare_tags_prob_list)
            if group is not None:
                group.prob_duplicates.append(dest_tags)
                group.prob_found_tags.append(found_tags)
            else:
                unique_dest_tracks.append(dest_tags)
        if (i + 1) % 10 == 0:
            counter.value += 10
        if i + 1 == len(dest_list):
            counter.value += (i % 10) + 1

    res = {}
    res['unique_dest_tracks'] = unique_dest_tracks
    res['groups'] = groups

    result.put(res)


def compare_by_tags(source_list: list, dest_list: list, tags_to_compare: list, dest_unique: dict, dest_dups: dict,
                    dup_tag: str, add_dup_tags=False):
    unique = []
    dups = []
    for dest_tags in dest_list:
        found = False
        for source_tags in source_list:
            if compare_tags(source_tags, dest_tags, tags_to_compare, False):
                found = True
                if add_dup_tags:
                    if dup_tag not in dest_tags:
                        dest_tags[dup_tag] = ""
                    dest_tags[dup_tag] += f'{source_tags["SPOTY_DUP_ID"]} : {",".join(tags_to_compare)}\n'
        if found:
            dups.append(dest_tags)
        else:
            unique.append(dest_tags)

    # move duplicates from unique to dups
    for item in dups:
        id = item['SPOTY_DUP_ID']
        if id in dest_unique:
            dest_dups[id] = item
            del dest_unique[id]


def move_audio_files_to_path(tags_list, path):
    moved_files = []
    for tags in tags_list:
        if 'SPOTY_FILE_NAME' in tags:
            old_file_name = tags['SPOTY_FILE_NAME']

            base_name = os.path.basename(old_file_name)

            new_file_name = os.path.join(path, base_name)
            if os.path.isfile(new_file_name):
                new_file_name = find_empty_file_name(new_file_name)

            os.rename(old_file_name, new_file_name)
            moved_files.append(new_file_name)

    return moved_files
