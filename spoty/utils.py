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

    for i, track in enumerate(tracks):
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
        tags['SOURCE'] = "Spotify"
        tags['SOURCEID'] = tags['SPOTIFY_TRACK_ID']

        tag_tracks.append(tags)

    return tag_tracks


def compare_two_tag_tracks(old_track, new_track, compare_tags, allow_missing=False):
    for tag in compare_tags:

        if not tag in old_track or not tag in new_track:
            if allow_missing:
                continue
            else:
                return False

        if new_track[tag] != old_track[tag]:
            return False

    return True