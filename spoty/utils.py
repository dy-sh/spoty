import os.path
import csv


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


def write_tracks_to_csv_file(tracks, file_name):
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    with open(file_name, 'w', encoding='utf-8-sig', newline='') as file:
        header = ['isrc', 'spotify_track_id', 'title', 'album', 'duration']
        writer = csv.writer(file)
        writer.writerow(header)

        for i, track in enumerate(tracks):
            track = track['track']
            track_title = get_track_artist_and_title(track)
            duration = track['duration_ms']
            isrc = ""
            try:
                isrc = track['external_ids']['isrc']
            except:
                pass
            album = ""
            try:
                album = track['album']['name']
            except:
                pass

            writer.writerow([isrc, track["id"], track_title, album, duration])


def read_tracks_from_csv_file(file_name):
    tracks_in_file = []

    with open(file_name, newline='', encoding='utf-8-sig') as file:
        reader = csv.reader(file)
        if sum(1 for row in reader) == 0:
            raise CSVFileEmpty()

    with open(file_name, newline='', encoding='utf-8-sig') as file:
        header = []
        reader = csv.reader(file)

        for i, row in enumerate(reader):
            # read header
            if (i == 0):
                header = row
                if "isrc" not in header and "spotify_track_id" not in header and "title" not in header:
                    raise CSVFileInvalidHeader()
                continue

            # read track
            if len(row) == 0:
                continue

            if "spotify_track_id" in header:
                id = row[header.index("spotify_track_id")]
                # log.debug(f'Importing track with spotify_track_id: {id}')
                tracks_in_file.append(id)
            elif "isrc" in header:
                isrc = row[header.index("isrc")]
                # log.debug(f'Importing track with isrc: {isrc}')
                # todo search by isrc
                pass
            elif "title" in header:
                title = row[header.index("title")]
                # log.debug(f'Importing track with title: {title}')
                # todo search by isrc
                pass

    return tracks_in_file
