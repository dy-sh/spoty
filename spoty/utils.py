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


def slugify_file_pah(text):
    # valid_chars = "-_.()=!@#$%%^&+ %s%s" % (string.ascii_letters, string.digits)
    # return ''.join(c for c in text if c in valid_chars).strip()

    valid_chars = '<>:"/\|?*'

    for char in valid_chars:
        text = text.replace(char, '')

    return text


def filter_duplicates(original_arr, new_arr):
    return list(filter(lambda id: id not in original_arr, new_arr))


def remove_duplicates(arr):
    good = []
    dup = []
    for item in enumerate(arr):
        if item in good:
            dup.append(item)
        else:
            good.append(item)
    return good, dup


def compare_two_tag_tracks(old_track, new_track, compare_tags, allow_missing=False):
    for tag in compare_tags:

        if not tag in old_track or not tag in new_track:
            if allow_missing:
                continue
            else:
                return False

        if tag == "LENGTH":
            if abs(int(old_track['LENGTH']) - int(new_track['LENGTH'])) > 5:
                return False
            else:
                continue

        if tag == "ARTIST":
            old_artist = old_track[tag].replace(',', ';').upper()
            old_artist = old_artist.split(';')
            new_artist = new_track[tag].replace(',', ';').upper()
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
            old_title = old_track[tag].upper()
            old_title = ''.join(char for char in old_title if char.isalnum())
            new_titile = new_track[tag].upper()
            new_titile = ''.join(char for char in new_titile if char.isalnum())
            if not new_titile.startswith(old_title) and not old_title.startswith(new_titile):
                return False
            else:
                continue

        if tag == "ALBUM":
            old_album = old_track[tag].upper()
            new_album = new_track[tag].upper()
            if not new_album.startswith(old_album) and not old_album.startswith(new_album):
                return False
            else:
                continue

        if old_track[tag] != new_track[tag]:
            return False

    return True


def find_duplicates_in_tag_tracks(all_tracks, tags_to_compare):
    if len(tags_to_compare) == 0:
        return

    duplicates = {}
    pattern = ""
    for tag in tags_to_compare:
        pattern += "%" + tag + "%,"
    pattern = pattern[:-1]

    groupped_tracks = group_tracks_by_pattern(pattern, all_tracks, "Unknown")

    for tags, tracks in groupped_tracks.items():
        if tags == "Unknown":
            continue
        if len(tracks) > 1:
            if not tags in duplicates:
                duplicates[tags] = []
            duplicates[tags].extend(tracks)

    skipped_tracks = groupped_tracks['Unknown'] if 'Unknown' in groupped_tracks else []

    return duplicates, all_tracks, skipped_tracks


def print_track_main_tags(track, include_playlist_info=False):
    if 'ISRC' in track: print(f'ISRC: {track["ISRC"]}')
    if 'ARTIST' in track: print(f'ARTIST: {track["ARTIST"]}')
    # if 'ALBUMARTIST' in track: print(f'ALBUMARTIST: {track["ALBUMARTIST"]}')
    if 'TITLE' in track: print(f'TITLE: {track["TITLE"]}')
    if 'ALBUM' in track: print(f'ALBUM: {track["ALBUM"]}')
    if 'GENRE' in track: print(f'GENRE: {track["GENRE"]}')
    if 'MOOD' in track: print(f'MOOD: {track["MOOD"]}')
    if 'OCCASION' in track: print(f'OCCASION: {track["OCCASION"]}')
    if 'RATING' in track: print(f'RATING: {track["RATING"]}')
    if 'COMMENT' in track: print(f'COMMENT: {track["COMMENT"]}')
    if 'BARCODE' in track: print(f'BARCODE: {track["BARCODE"]}')
    # if 'BPM' in track: print(f'BPM: {track["BPM"]}')
    # if 'FILEOWNER' in track: print(f'FILEOWNER: {track["FILEOWNER"]}')
    if 'LENGTH' in track: print(f'LENGTH: {track["LENGTH"]}')
    # if 'QUALITY' in track: print(f'QUALITY: {track["QUALITY"]}')
    if 'SPOTIFY_TRACK_ID' in track: print(f'SPOTIFY_TRACK_ID: {track["SPOTIFY_TRACK_ID"]}')
    # if 'SPOTIFY_RELEASE_ID' in track: print(f'SPOTIFY_RELEASE_ID: {track["SPOTIFY_RELEASE_ID"]}')
    if 'SOURCE' in track: print(f'SOURCE: {track["SOURCE"]}')
    if 'SOURCEID' in track: print(f'SOURCEID: {track["SOURCEID"]}')
    # if 'TEMPO' in track: print(f'TEMPO: {track["TEMPO"]}')
    if 'YEAR' in track: print(f'YEAR: {track["YEAR"]}')

def print_tracks(tags_list, tags_to_print):
    for i, track in enumerate(tags_list):
        print(
            f'--------------------- TRACK {i + 1} / {len(tags_list)} ---------------------')
        print_track_tags(track, tags_to_print)

    if len(tags_list) > 0:
        print("-------------------------------------------------------------------------------------")

def print_track_tags(track, tags_to_print):
    for tag in tags_to_print:
        if tag.upper() in track:
            print(f'{tag}: {track[tag]}')



def filter_tracks_which_have_all_tags(track_tags, filter_tags):
    filtered = []
    for track in track_tags:
        if check_track_have_all_tags(track, filter_tags):
            filtered.append(track)
    return filtered


def filter_tracks_which_not_have_any_of_tags(track_tags, filter_tags):
    filtered = []
    for track in track_tags:
        if not check_track_have_all_tags(track, filter_tags):
            filtered.append(track)
    return filtered


def check_track_have_all_tags(track, tags):
    for tag in tags:
        if not tag.upper() in track:
            return False
    return True


def group_tracks_by_pattern(pattern, tracks, not_found_tag_name="Unknown"):
    groups = {}

    for track in tracks:
        group_name = ""
        tag_name = ""
        building_tag = False
        for c in pattern:
            if c == "%":
                building_tag = not building_tag
                if not building_tag:
                    tag = track[tag_name] if tag_name in track else not_found_tag_name
                    group_name += str(tag)
                    tag_name = ""
            else:
                if building_tag:
                    tag_name += c
                    tag_name = tag_name.upper()
                else:
                    group_name += c

        if not group_name in groups:
            groups[group_name] = []

        groups[group_name].append(track)

    return groups


def reorder_tag_keys(keys):
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


def is_valid_path(path):
    return os.path.isdir(path)


def is_valid_file(path):
    return os.path.isfile(path)
