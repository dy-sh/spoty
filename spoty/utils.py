import os.path
import csv
import spoty.local


class CSVImportException(Exception):
    """Base class for exceptions when importing CSV file."""
    pass


class CSVFileEmpty(CSVImportException):
    """File is empty."""
    pass


class CSVFileInvalidHeader(CSVImportException):
    """The header of csv table does not contain any of the required fields."""
    pass


def get_track_artist_and_title(track):
    artists = list(map(lambda artist: artist['name'], track['artists']))
    artists_str = ', '.join(artists)
    artists_str.replace(' - ', ' ')
    title = track['name'].replace(' - ', ' ')
    return f"{artists_str} - {title}"


def get_track_ids(tracks):
    if len(tracks) == 0:
        return []
    else:
        return [item['track']['id'] for item in tracks]


def check_is_playlist_URI(uri):
    return uri.startswith("https://open.spotify.com/playlist/")


def parse_playlist_id(id_or_url):
    if (id_or_url.startswith("https://open.spotify.com/playlist/")):
        id_or_url = id_or_url.split('/playlist/')[1]
        id_or_url = id_or_url.split('?')[0]
    return id_or_url


def parse_track_id(id_or_url):
    if (id_or_url.startswith("https://open.spotify.com/track/")):
        id_or_url = id_or_url.split('/track/')[1]
        id_or_url = id_or_url.split('?')[0]
    return id_or_url


def slugify_file_pah(text):
    # valid_chars = "-_.()=!@#$%%^&+ %s%s" % (string.ascii_letters, string.digits)
    # return ''.join(c for c in text if c in valid_chars).strip()

    valid_chars = '<>:"/\|?*'

    for char in valid_chars:
        text = text.replace(char, '')

    return text


def get_playlist_file_name(playlist_name, playlist_id, path, avoid_filenames):
    playlist_name = slugify_file_pah(playlist_name)
    if (len(playlist_name) == 0):
        playlist_name = playlist_id
    full_file_name = os.path.join(path, playlist_name + ".csv")

    if full_file_name in avoid_filenames:
        full_file_name = get_playlist_file_name(playlist_name + " (1)", playlist_id, path, avoid_filenames)

    return full_file_name


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

def read_tags_from_spotify_tracks(tracks):
    tag_tracks = []

    for track in tracks:
        tags=read_tags_from_spotify_track(track)
        tag_tracks.append(tags)

    return tag_tracks

def read_tags_from_spotify_track(track):
    if "track" in track:
        track = track['track']

    tags = {}

    try:
        tags['ISRC'] = track['external_ids']['isrc']
    except:
        pass

    try:
        artists = list(map(lambda artist: artist['name'], track['artists']))
        tags['ARTIST'] = ';'.join(artists)
    except:
        pass

    tags['TITLE'] = track['name']

    try:
        tags['ALBUM'] = track['album']['name']
    except:
        pass

    tags['LENGTH'] = track['duration_ms']

    try:
        tags['SPOTIFY_RELEASE_ID'] = track['album']['id']
    except:
        pass

    tags['WWWAUDIOFILE'] = track['external_urls']['spotify']

    tags['SPOTIFY_TRACK_ID'] = track["id"]

    tags['EXPLICIT'] = track['explicit']

    tags['TRACK'] = track['track_number']

    try:
        tags['YEAR'] = track['album']['release_date']
    except:
        pass

    # PREVIEW_URL=track['preview_url']
    # tags['SOURCE'] = "Spotify"
    # tags['SOURCEID'] = tags['SPOTIFY_TRACK_ID']

    return tags




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


def filter_spotify_tracks_which_have_all_tags(spotify_track, filter_tags):
    filtered = []
    for track in spotify_track:
        tags = spoty.utils.read_tags_from_spotify_track(track)
        if check_track_have_all_tags(tags, filter_tags):
            filtered.append(track)
    return filtered


def filter_spotify_tracks_which_not_have_any_of_tags(spotify_track, filter_tags):
    filtered = []
    for track in spotify_track:
        tags = spoty.utils.read_tags_from_spotify_track(track)
        if not check_track_have_all_tags(tags, filter_tags):
            filtered.append(track)
    return filtered

def check_track_have_all_tags(track, tags):
    for tag in tags:
        if not tag.upper() in track:
            return False
    return True
