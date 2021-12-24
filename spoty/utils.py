import os.path
from spoty import settings

class SpotyContext:
    tags_list: list = []
    summary: list = []


class FakeContext:
    obj: None


tag_allies = [
    ['YEAR', 'DATE'],
    ['TRACK', 'TRACKNUMBER'],
    ['DISK', 'DISKNUMBER']
]

spoty_tags = \
    [
        'SPOTY_DUP_ID',
        'SPOTY_DUP',
        'SPOTY_DUPLICATE_GROUP',
        'SPOTY_SOURCE',
        'SPOTY_PLAYLIST_NAME',
        'SPOTY_PLAYLIST_ID',
        'SPOTY_PLAYLIST_INDEX',
        'SPOTY_FILE_NAME',
        'SPOTY_TRACK_ID',
        'SPOTY_TRACK_ADDED',
        'SPOTY_LENGTH',
        # spotify specific
        'SPOTIFY_TRACK_ID',
        'SPOTIFY_ALBUM_ID',
        # deezer specific
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
        'BARCODE',
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


def tuple_to_list(some_tuple: tuple):
    l = []
    l.extend(some_tuple)
    return l

def dict_to_list(some_dics: dict):
    l = []
    for key,value in some_dics.items():
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


def remove_tags_duplicates(tags_list: list, tags_to_compare: list, allow_missing=False):
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


def compare_tags(src_tags: dict, dest_tags: dict, tags_to_compare: list, allow_missing=False):
    for tag in tags_to_compare:

        if not tag in src_tags or not tag in dest_tags:
            if allow_missing:
                continue
            else:
                return False

        if tag == 'SPOTY_LENGTH':
            if abs(int(src_tags['SPOTY_LENGTH']) - int(dest_tags['SPOTY_LENGTH'])) > settings.SPOTY.COMPARE_LENGTH_DIFF_SECS:
                return False
            else:
                continue

        if tag == "ARTIST":
            old_artist = src_tags[tag].replace(',', ';').upper()
            old_artist = old_artist.split(';')
            new_artist = dest_tags[tag].replace(',', ';').upper()
            new_artist = new_artist.split(';')
            found = False
            for old in old_artist:
                if old in new_artist:
                    found = True
            if not found:
                return False
            else:
                continue

        if tag == "TITLE":
            old_title = src_tags[tag].upper()
            old_title = ''.join(char for char in old_title if char.isalnum())
            new_titile = dest_tags[tag].upper()
            new_titile = ''.join(char for char in new_titile if char.isalnum())
            if not new_titile.startswith(old_title) and not old_title.startswith(new_titile):
                return False
            else:
                continue

        if tag == "ALBUM":
            old_album = src_tags[tag].upper()
            new_album = dest_tags[tag].upper()
            if not new_album.startswith(old_album) and not old_album.startswith(new_album):
                return False
            else:
                continue

        if src_tags[tag] != dest_tags[tag]:
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


def print_tags_list(tags_list: list, print_pattern: str, grouping_pattern: str):
    if len(tags_list) == 0:
        return

    grouped_tags = group_tags_by_pattern(tags_list, grouping_pattern)

    for group, tags_l in grouped_tags.items():
        print(f'\n------------------------- {group}:')
        for i, tags in enumerate(tags_l):
            txt = parse_pattern(tags, print_pattern)
            print(txt)


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
        if key == 'SPOTY_LENGTH':
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
