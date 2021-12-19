import os.path

tag_allies = [
    ['YEAR', 'DATE'],
    ['TRACK', 'TRACKNUMBER'],
    ['DISK', 'DISKNUMBER']
]

spoty_tags = \
    [
        'SPOTY_DUPLICATE_GROUP',
        'SPOTY_PLAYLIST_SOURCE',
        'SPOTY_PLAYLIST_NAME',
        'SPOTY_PLAYLIST_ID',
        'SPOTY_PLAYLIST_INDEX',
        'SPOTY_FILE_NAME',
        'SPOTY_TRACK_ID',
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


def is_valid_path(path):
    return os.path.isdir(path)


def is_valid_file(path):
    return os.path.isfile(path)


def slugify_file_pah(text):
    # valid_chars = "-_.()=!@#$%%^&+ %s%s" % (string.ascii_letters, string.digits)
    # return ''.join(c for c in text if c in valid_chars).strip()

    valid_chars = '<>:"/\|?*'

    for char in valid_chars:
        text = text.replace(char, '')

    return text


def filter_duplicates(src_arr, dest_arr):
    return list(filter(lambda id: id not in src_arr, dest_arr))


def remove_duplicates(arr):
    good = []
    dup = []
    for item in arr:
        if item in good:
            dup.append(item)
        else:
            good.append(item)
    return good, dup


def remove_exist(exist_arr, new_arr):
    good = []
    dup = []
    for item in new_arr:
        if item in exist_arr:
            dup.append(item)
        else:
            good.append(item)
    return good, dup


def compare_tags(src_tags, dest_tags, compare_tags, allow_missing=False):
    for tag in compare_tags:

        if not tag in src_tags or not tag in dest_tags:
            if allow_missing:
                continue
            else:
                return False

        if tag == "LENGTH":
            if abs(int(src_tags['LENGTH']) - int(dest_tags['LENGTH'])) > 5:
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


def find_duplicates_in_tags(tags_list, compare_tags):
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


def print_main_tags(tags):
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
    if 'LENGTH' in tags: print(f'LENGTH: {tags["LENGTH"]}')
    if 'SPOTIFY_TRACK_ID' in tags: print(f'SPOTIFY_TRACK_ID: {tags["SPOTIFY_TRACK_ID"]}')
    if 'SOURCE' in tags: print(f'SOURCE: {tags["SOURCE"]}')
    if 'SOURCEID' in tags: print(f'SOURCEID: {tags["SOURCEID"]}')
    if 'YEAR' in tags: print(f'YEAR: {tags["YEAR"]}')


def print_tags_list(tags_list, print_pattern, grouping_pattern):
    if len(tags_list) == 0:
        return

    grouped_tags = group_tags_by_pattern(tags_list, grouping_pattern)

    for group, tags_l in grouped_tags.items():
        print(f'\n------------------------- {group}:')
        for i, tags in enumerate(tags_l):
            txt = parse_pattern(tags, print_pattern)
            print(txt)


def check_tag_has_allies(tag):
    for allies in tag_allies:
        if tag in allies:
            return True
    return False


def get_tag_allies(tag, include_source_tag=True):
    res = []
    for allies in tag_allies:
        if tag in allies:
            res = allies.copy()

    if tag in res:
        res.remove(tag)

    if include_source_tag:
        res.append(tag)
    return res


def print_tags(tags, tags_to_print):
    for tag in tags_to_print:
        allies = get_tag_allies(tag, True)
        for a in allies:
            if a.upper() in tags:
                print(f'{a}: {tags[a]}')


def add_playlist_index_from_playlist_names(tags_list):
    res = []
    groups = group_tags_by_pattern(tags_list, "%SPOTY_PLAYLIST_NAME%")
    for group, g_tags_list in groups.items():
        for i, tags in enumerate(g_tags_list):
            tags['SPOTY_PLAYLIST_INDEX'] = i + 1
            res.append(tags)
    return res


def filter_tags_list_have_tags(tags_list, filter_tags):
    filtered = []
    for tags in tags_list:
        if check_all_tags_exist(tags, filter_tags):
            filtered.append(tags)
    return filtered


def filter_tags_list_have_no_tags(tags_list, filter_tags):
    filtered = []
    for tags in tags_list:
        if not check_all_tags_exist(tags, filter_tags):
            filtered.append(tags)
    return filtered


def check_all_tags_exist(tags, tags_to_check):
    for tag in tags_to_check:
        if not tag.upper() in tags:
            return False
    return True


def group_tags_by_pattern(tags_list, pattern, not_found_tag_name="Unknown"):
    groups = {}

    for tags in tags_list:
        group_name = parse_pattern(tags, pattern)

        if not group_name in groups:
            groups[group_name] = []

        groups[group_name].append(tags)

    return groups


def parse_pattern(tags, pattern):
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


def reorder_tag_keys_main_first(keys):
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


def get_missing_tags(exist_tags, new_tags):
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
