import deezer.errors
from spoty import settings
from deezer import Deezer
from spoty import log
import spoty.utils
import os.path
import click
import time
import re


DEEZER_APP_ID = settings.default.APP_ID
DEEZER_APP_SECRET = settings.default.APP_SECRET
DEEZER_ACCESS_TOKEN = settings.default.ACCESS_TOKEN
DEEZER_REDIRECT_URI = settings.REDIRECT_URI
arl_file_name = os.path.join(settings.config_path, '.arl')

dz = None


def get_dz():
    global dz
    if dz is None:
        dz = Deezer()
    return dz


def request_valid_arl():
    while True:
        arl = input("Paste here your arl:")
        if get_dz().login_via_arl(arl.strip()): break
    return arl


def check_arl():
    if os.path.isfile(arl_file_name):
        with open(arl_file_name, 'r') as f:
            arl = f.readline().rstrip("\n").strip()
        if not get_dz().login_via_arl(arl): arl = request_valid_arl()
    else:
        arl = request_valid_arl()
    with open(arl_file_name, 'w') as f:
        f.write(arl)


def create_folder(folder_name):
    current_directory = os.getcwd()
    final_directory = os.path.join(current_directory, folder_name)
    if not os.path.exists(final_directory):
        os.makedirs(final_directory)


def read_file(file_name):
    try:
        file = open(file_name, encoding='utf-8-sig')
        lines = list(file)
        file.close()
    except:
        print("Cant open file: " + file_name)
        raise
    return lines


def get_track_artist_and_title(track):
    artist = "Unknown"
    title = "Unknown"
    try:
        artist = track["ART_NAME"]
    except:
        pass

    try:
        title = track["SNG_TITLE"]
    except:
        pass

    return f"{artist} - {title}"


def filter_duplicates(original_arr, new_arr):
    return list(filter(lambda id: id not in original_arr, new_arr))


def remove_duplicates(arr):
    good = []
    for item in arr:
        if item not in good:
            good.append(item)
    return good


def get_track_ids(tracks):
    if len(tracks) == 0:
        return []
    else:
        return [str(track['SNG_ID']) for track in tracks]


def parse_playlist_id(id_or_url: str):
    id_or_url = str(id_or_url)
    if id_or_url.startswith("https://www.deezer.com/") and "/playlist/" in id_or_url:
        id_or_url = id_or_url.split('/playlist/')[1]
        id_or_url = id_or_url.split('?')[0]
    return id_or_url


def parse_track_id(id_or_url: str):
    id_or_url = str(id_or_url)
    if id_or_url.startswith("https://www.deezer.com/") and "/track/" in id_or_url:
        id_or_url = id_or_url.split('/track/')[1]
        id_or_url = id_or_url.split('?')[0]
    return id_or_url


def create_playlist(name):
    log.info(f'Creating new playlist')

    # "Quota exceeded for playlist_create" message is very often received.
    # todo: just send create playlist request with official API

    WAITING_DELAY = 60

    while True:
        try:
            playlist_id = get_dz().gw.create_playlist(name)
            return playlist_id
        except deezer.errors.GWAPIError as e:
            if e.args[0] == '{"QUOTA_ERROR": "Quota exceeded for playlist_create"}':
                click.echo(f"Quota exceeded for playlist_create. Waiting {WAITING_DELAY} seconds ...")
                time.sleep(WAITING_DELAY)


def get_playlist(playlist_id):
    playlist_id = parse_playlist_id(playlist_id)

    log.info(f'Requesting playlist {playlist_id}')

    playlist = get_dz().gw.get_playlist_page(playlist_id)
    return playlist['DATA']


def get_playlist_with_full_list_of_tracks(playlist_id):
    playlist_id = parse_playlist_id(playlist_id)

    log.info(f'Collecting playlist {playlist_id}')

    playlist = get_dz().gw.get_playlist_page(playlist_id)
    tracks = get_dz().gw.get_playlist_tracks(playlist_id)

    playlist = playlist['DATA']

    log.debug(f'Playlist have {len(tracks)} tracks (playlist name: "{playlist["TITLE"]}")')

    return tracks, playlist


def get_playlists_with_full_list_of_tracks(playlist_ids):
    for i in range(len(playlist_ids)):
        playlist_ids[i] = parse_playlist_id(playlist_ids[i])

    playlists_dict = {}
    with click.progressbar(playlist_ids, label='Reading playlists') as bar:
        for playlist_id in bar:
            playlists_dict[playlist_id] = []

            tracks = get_dz().gw.get_playlist_tracks(playlist_id)
            playlists_dict[playlist_id].extend(tracks)

    return playlists_dict


def get_list_of_playlists():
    return get_list_of_user_playlists()


def get_list_of_user_playlists(user_id=None):
    if user_id is None:
        user_data = get_dz().gw.get_user_data()
        user_id = user_data['USER']['USER_ID']
    playlists = get_dz().gw.get_user_playlists(user_id)
    return playlists


def delete_playlist(playlist_ids, confirm=False):
    deleted_playlists = []
    for playlist_id in playlist_ids:
        playlist_id = parse_playlist_id(playlist_id)

        log.info(f'Deleting playlist {playlist_id}')

        playlist = get_playlist(playlist_id)
        if playlist == None:
            log.info(f'Playlist {playlist_id} does not exist.')
            continue

        if not confirm:
            if not click.confirm(f'Are you sure you want to delete playlist "{playlist["TITLE"]}"?'):
                log.info("Playlist not deleted. Canceled by user.")
                continue
            click.echo()

        res = get_dz().gw.delete_playlist(playlist_id)
        if res:
            log.success(f'Playlist {playlist_id} deleted"')
            deleted_playlists.append(playlist_id)
        else:
            log.error(f'Playlist {playlist_id} not deleted"')

    return deleted_playlists


def delete_all_playlist(confirm=False):
    log.info(f'Deleting all playlist')

    playlists = get_list_of_playlists()

    if len(playlists) <= 1:
        log.debug("User has no playlists.")
        return []

    if not confirm:
        if not click.confirm(f'Are you sure you want to delete all {len(playlists)} playlists?'):
            log.info("Playlists not deleted. Canceled by user.")
            return []

    ids = [pl['id'] for pl in playlists]
    deleted_playlists = delete_playlist(ids, True)

    return deleted_playlists


def find_tracks_by_isrc(isrcs_list):
    isrcs_list = list(filter(lambda isrc: len(isrc) > 0, isrcs_list))
    isrcs_list = remove_duplicates(isrcs_list)

    log.info(f'Finding tacks by ISRCs (count: {len(isrcs_list)})')

    # for dup in duplicates:
    #     log.warning(f'A track with IRSC "{dup}" duplicated. Duplicate removed.')

    not_found_isrcs = []
    tracks = []

    for i, isrc in enumerate(isrcs_list):
        try:
            track = get_dz().api.get_track_by_ISRC(isrc)
            tracks.append(track)
            title = get_track_artist_and_title(track)
            log.debug(f'Track found: ISRC: {isrc} ID: {track["id"]} TITLE: "{title.encode("utf-8")}"')
        except deezer.errors.DataException as e:
            log.debug(f'Track not found: ISRC: {isrc}"')
            not_found_isrcs.append(isrc)

    return tracks, not_found_isrcs


def add_tracks_to_playlist(playlist_id, track_ids, allow_duplicates=False):
    playlist_id = parse_playlist_id(playlist_id)
    track_ids = remove_duplicates(track_ids)

    for i in range(len(track_ids)):
        track_ids[i] = parse_track_id(track_ids[i])

    log.info(f'Adding {len(track_ids)} tracks to playlist {playlist_id}')

    playlist = get_playlist(playlist_id)

    if not allow_duplicates:
        tracks, playlist = get_playlist_with_full_list_of_tracks(playlist_id)
        existing_ids = get_track_ids(tracks)
        new_ids = filter_duplicates(existing_ids, track_ids)
        if len(track_ids) != len(new_ids):
            log.debug(f'{len(track_ids) - len(new_ids)}/{len(track_ids)} tracks already exist and will be skipped.')
            track_ids = new_ids

    tracks_added = []
    tracks_copy = track_ids.copy()

    # split by 100 tracks for one request
    tracks_count = 0
    playlist_index = 1
    while len(tracks_copy) > 0:
        tracks_to_proceed = tracks_copy[0:50]
        del tracks_copy[:50]

        get_dz().gw.add_songs_to_playlist(playlist_id, tracks_to_proceed)
        tracks_added.extend(tracks_to_proceed)

        # split by 2000 tracks for one playlist
        tracks_count += len(tracks_to_proceed)
        if tracks_count >= 2000 and len(tracks_copy) > 0:
            tracks_count = 0
            playlist_index += 1
            title = f'{playlist["title"]} {playlist_index}'
            playlist = create_playlist(title)
            print(f'New playlist created. ID: {playlist["id"]} TITLE: {title}')

    log.success(f'Adding tracks complete (tracks added: {len(tracks_added)}')

    return tracks_added


def find_playlist_by_name(name):
    playlists = get_list_of_playlists()
    return list(filter(lambda pl: pl['title'] == name, playlists))
