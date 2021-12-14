from spoty import sp
from spoty import log
import spoty.utils
import os.path
import click
import time


def get_playlist_with_full_list_of_tracks(playlist_id):
    playlist_id = spoty.utils.parse_playlist_id(playlist_id)

    log.info(f'Collecting playlist {playlist_id}')

    playlist = sp.playlist(playlist_id)
    total_tracks = playlist["tracks"]["total"]
    tracks = playlist["tracks"]["items"]

    log.debug(f'Playlist have {total_tracks} tracks (playlist name: "{playlist["name"]}")')
    log.debug(f'Collected {len(tracks)}/{total_tracks} tracks')

    # if playlist is larger than 100 songs, continue loading it until end
    result = playlist
    while len(tracks) < total_tracks:
        if 'next' in result:
            result = sp.next(result)
        else:
            result = sp.next(result["tracks"])
        tracks.extend(result['items'])
        log.debug(f'Collected {len(tracks)}/{total_tracks} tracks')

    playlist["tracks"]["items"] = tracks

    return playlist


def get_playlist(playlist_id):
    playlist_id = spoty.utils.parse_playlist_id(playlist_id)

    log.info(f'Requesting playlist {playlist_id}')

    playlist = sp.playlist(playlist_id)

    return playlist


def get_list_of_playlists(only_owned_by_user=True):
    user_id = sp.me()['id']
    playlists = []

    log.info(f'Collecting playlists for current user ({user_id})')

    with click.progressbar(length=100, label='Collecting playlists') as bar:

        # load first 50 playlists
        result = sp.current_user_playlists(limit=50)
        playlists.extend(result['items'])
        total_playlists = result['total']

        log.debug(f'Collected {len(playlists)}/{total_playlists}')

        bar.length = total_playlists
        bar.update(len(playlists))

        # load next 50 playlists
        while result['next']:
            result = sp.next(result)
            playlists.extend(result['items'])
            bar.update(len(playlists))

            log.debug(f'Collected {len(playlists)}/{total_playlists}')

    if (only_owned_by_user):
        playlists = list(filter(lambda pl: pl['owner']['id'] == user_id, playlists))

    return playlists


def find_playlist_by_name(name, only_owned_by_user=True):
    playlists = get_list_of_playlists(only_owned_by_user)
    return list(filter(lambda pl: pl['name'] == name, playlists))


def get_list_of_user_playlists(user_id: str):
    log.info(f'Collecting playlists for user {user_id}')

    with click.progressbar(length=100, label='Collecting playlists') as bar:
        # load first 50 playlists
        playlists = []
        result = sp.user_playlists(user=user_id, limit=50)
        playlists.extend(result['items'])
        total_playlists = result['total']

        log.debug(f'Collected {len(playlists)}/{total_playlists} playlists')

        bar.length = total_playlists
        bar.update(len(playlists))

        # load next 50 playlists
        while result['next']:
            result = sp.next(result)
            playlists.extend(result['items'])
            bar.update(len(playlists))

            log.debug(f'Collected {len(playlists)}/{total_playlists} playlists')

        return playlists


def create_playlist(name):
    log.info(f'Creating new playlist')

    user_id = sp.me()['id']
    new_playlist = sp.user_playlist_create(user_id, name)
    id = new_playlist['id']

    log.success(f'New playlist created (id: {id}, name: "{name}")')

    return id


def copy_playlist(playlist_id):
    log.info(f'Creating a copy of playlist {playlist_id}')

    playlist = get_playlist_with_full_list_of_tracks(playlist_id)
    tracks = playlist["tracks"]["items"]

    ids = spoty.utils.get_track_ids(tracks)
    new_playlist_id = create_playlist(playlist['name'])
    tracks_added = add_tracks_to_playlist(new_playlist_id, ids, True)

    log.success(f"Playlist copy completed ({len(tracks_added)} tracks added).")

    return new_playlist_id, tracks_added


def get_tracks_of_playlist(playlist_id):
    playlist_id = spoty.utils.parse_playlist_id(playlist_id)

    log.info(f'Collecting tracks from playlist {playlist_id}')

    # load the first 100 songs
    tracks = []
    result = sp.playlist_items(playlist_id, additional_types=['track'], limit=100)
    tracks.extend(result['items'])

    log.debug(f'Collected {len(tracks)}/{result["total"]} tracks')

    # if playlist is larger than 100 songs, continue loading it until end
    while result['next']:
        result = sp.next(result)
        tracks.extend(result['items'])
        log.debug(f'Collected {len(tracks)}/{result["total"]} tracks')

    # removing invalid tracks without ids (was deleted from spotify library)
    new_tracks = []
    for track in tracks:
        try:
            id = track['track']['id']
            assert id is not None, "Track id is None"
            new_tracks.append(track)
        except:
            pass

    if len(new_tracks) != len(tracks):
        log.warning(f'Playlist {playlist_id} has {len(tracks) - len(new_tracks)} invalid tracks')

    return new_tracks


def add_tracks_to_playlist(playlist_id, track_ids, allow_duplicates=False):
    playlist_id = spoty.utils.parse_playlist_id(playlist_id)

    track_ids = list(track_ids)

    for i in range(len(track_ids)):
        track_ids[i] = spoty.utils.parse_track_id(track_ids[i])

    log.info(f'Adding {len(track_ids)} tracks to playlist {playlist_id}')

    if not allow_duplicates:
        tracks = get_tracks_of_playlist(playlist_id)
        existing_ids = spoty.utils.get_track_ids(tracks)
        new_ids = spoty.utils.filter_duplicates(existing_ids, track_ids)
        if len(track_ids) != len(new_ids):
            log.debug(f'{len(track_ids) - len(new_ids)}/{len(track_ids)} tracks already exist and will be skipped.')
            track_ids = new_ids

    tracks_added = []

    i = 0
    next_tracks = []
    while i < len(track_ids):
        next_tracks.append(track_ids[i])
        if len(next_tracks) == 100 or i == len(track_ids) - 1:
            sp.playlist_add_items(playlist_id, next_tracks)
            tracks_added.extend(next_tracks)
            log.debug(f'{len(next_tracks)} tracks added to playlist')
            next_tracks = []
        i += 1

    log.success(f'Adding tracks complete (tracks added: {len(next_tracks)}')

    return tracks_added


def export_playlist_to_file(playlist_id, path, overwrite=False, avoid_filenames=[]):
    playlist_id = spoty.utils.parse_playlist_id(playlist_id)

    log.info(f'Exporting playlist {playlist_id}')

    playlist = get_playlist_with_full_list_of_tracks(playlist_id)

    file_name = spoty.utils.get_playlist_file_name(playlist["name"], playlist_id, path, avoid_filenames)

    if os.path.isfile(file_name) and not overwrite:
        time.sleep(0.2)  # waiting progressbar updating
        if not click.confirm(f'\nFile "{file_name}" already exist. Overwrite?'):
            log.info(f'Canceled by user (file already exist)')
            return None

    tracks = playlist["tracks"]["items"]

    spoty.utils.write_tracks_to_csv_file(tracks, file_name)

    log.success(f'Playlist exported (file: "{file_name}")')

    return file_name


def import_playlist_from_file(file_name, append_if_exist=False, allow_duplicates=False):
    log.info(f'Importing playlist from file "{file_name}"')
    tracks_added = []

    playlist_id = None
    base = os.path.basename(file_name)
    playlist_name = os.path.splitext(base)[0]

    if append_if_exist:
        found_playlists = find_playlist_by_name(playlist_name)
        if len(found_playlists) > 0:
            if len(found_playlists) > 1:
                if not click.confirm(
                        f'\n{len(found_playlists)} playlists found with name "{playlist_name}". Choose the first one and continue?'):
                    log.info(f'Canceled by user (more than one playlists found with name "{playlist_name})"')
                    return 0
            playlist_id = found_playlists[0]['id']

    if playlist_id is None:
        playlist_id = create_playlist(playlist_name)

    tracks_in_file = spoty.utils.read_playlist_from_file(file_name)

    if len(tracks_in_file) > 0:
        tracks_added = add_tracks_to_playlist(playlist_id, tracks_in_file, allow_duplicates)

    log.success(f'Playlist imported (new tracks: "{len(tracks_added)}")')

    return playlist_id, tracks_added, tracks_in_file
