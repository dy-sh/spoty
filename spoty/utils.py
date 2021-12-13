import os.path


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


def get_not_liked_tracks(tracks, likes):
    result = []
    for i in range(len(tracks)):
        if not likes[i]:
            result.append(tracks[i])
    return result


def get_liked_tracks(tracks, likes):
    result = []
    for i in range(len(tracks)):
        if likes[i]:
            result.append(tracks[i])
    return result


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
