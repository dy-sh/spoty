from spoty import log
import spoty.utils
import spoty.csv_playlist
import os.path
import click
import time
import re
from spoty import settings, config_path
from spotipy.oauth2 import SpotifyOAuth
import spotipy
import datetime

SPOTIFY_CLIENT_ID = settings.default.SPOTIFY_CLIENT_ID
SPOTIFY_CLIENT_SECRET = settings.default.SPOTIFY_CLIENT_SECRET
REDIRECT_URI = settings.SPOTIFY.REDIRECT_URI

sp = None

cache_file_name = os.path.join(config_path, ".cache")


def get_sp():
    global sp
    if sp is None:
        sp = spotipy.Spotify(requests_timeout=30, auth_manager=SpotifyOAuth(
            SPOTIFY_CLIENT_ID,
            SPOTIFY_CLIENT_SECRET,
            REDIRECT_URI,
            scope="user-library-read user-library-modify playlist-modify-private playlist-read-private playlist-modify-public",
            cache_path=cache_file_name
        ))
    return sp


def get_tracks_from_playlists(playlist_ids: list, add_spoty_tags=True):
    all_tracks = []
    all_tags_list = []
    all_received_playlists = []

    requested_playlists = []

    with click.progressbar(playlist_ids, label=f'Reading tracks in {len(playlist_ids)} Spotify playlists') as bar:
        for playlist_id in bar:

            # remove already requested playlists
            if playlist_id in requested_playlists:
                click.echo(f'Spotify playlist {playlist_id} requested twice. In will be skipped.')
                continue

            playlist = get_playlist_with_full_list_of_tracks(playlist_id, add_spoty_tags)
            requested_playlists.append(playlist_id)

            tracks = playlist['tracks']['items']

            tags = read_tags_from_spotify_tracks(tracks)

            all_tracks.extend(tracks)
            all_tags_list.extend(tags)
            all_received_playlists.append(playlist_id)

    return all_tracks, all_tags_list, all_received_playlists


def get_tracks_of_spotify_user(user_id: str, playlists_names_regex: str = None):
    user_id = parse_user_id(user_id)
    if user_id == 'me':
        playlists = get_list_of_playlists()
        click.echo(f'You have {len(playlists)} playlists in Spotify library')
    else:
        playlists = get_list_of_user_playlists(user_id)
        click.echo(f'User {user_id} has {len(playlists)} playlists in Spotify library')

    if playlists_names_regex is not None:
        playlists = list(filter(lambda pl: re.findall(playlists_names_regex, pl['name']), playlists))

    if len(playlists) == 0:
        return [], [], []

    ids = get_playlists_ids(playlists)
    tracks, tags, playlists = get_tracks_from_playlists(ids)

    return tracks, tags, playlists


def find_track_by_isrc(isrc: str, length=None, length_tolerance=settings.SPOTY.COMPARE_LENGTH_TOLERANCE_SEC):
    tracks = find_track_by_query(f'isrc:{isrc}', length, length_tolerance)
    return tracks


def find_track_id_by_isrc(isrc: str, length=None, length_tolerance=settings.SPOTY.COMPARE_LENGTH_TOLERANCE_SEC):
    track = find_track_by_isrc(isrc, length, length_tolerance)
    return track['id'] if track is not None else None


def find_track_by_artist_and_title(artist: str, title: str, length=None,
                                   length_tolerance=settings.SPOTY.COMPARE_LENGTH_TOLERANCE_SEC):
    track = find_track_by_query(f'track:{title} artist:{artist}', length, length_tolerance)
    return track


def find_track_by_query(query: str, length=None, length_tolerance=settings.SPOTY.COMPARE_LENGTH_TOLERANCE_SEC):
    res = get_sp().search(query)
    try:
        tracks = res['tracks']['items']
        if length is not None:
            for track in tracks:
                if abs(int(track['duration_ms']) / 1000 - int(length)) < length_tolerance:
                    return track
            while res['tracks']['next']:
                res = get_sp().next(res['tracks'])
                tracks = res['tracks']['items']
                for track in tracks:
                    if abs(int(track['duration_ms']) / 1000 - int(length)) < length_tolerance:
                        return track
            return None

        return tracks
    except:
        pass
    return None


def find_track_by_id(id: str):
    track = get_sp().track(id)
    return track


def find_track_id_by_artist_and_title(artist: str, title: str, length=None,
                                      length_tolerance=settings.SPOTY.COMPARE_LENGTH_TOLERANCE_SEC):
    track = find_track_by_artist_and_title(artist, title, length, length_tolerance)
    return track['id'] if track is not None else None


def find_missing_track_ids(tags_list: list, ignore_duration=False):
    found = []
    not_found = []

    tracks_without_id = [tags for tags in tags_list if not 'SPOTIFY_TRACK_ID' in tags]

    if len(tracks_without_id) == 0:
        return tags_list, []

    with click.progressbar(tags_list, length=len(tracks_without_id),
                           label=f'Identifying {len(tracks_without_id)} tracks') as bar:
        for tags in tags_list:
            if "SPOTIFY_TRACK_ID" in tags:
                tags['SPOTY_FOUND_BY'] = 'SPOTIFY_TRACK_ID'
                found.append(tags)
                continue

            if "ISRC" in tags:
                if not ignore_duration and 'SPOTY_LENGTH' in tags:
                    id = find_track_id_by_isrc(tags['ISRC'], tags['SPOTY_LENGTH'])
                else:
                    id = find_track_id_by_isrc(tags['ISRC'])
                if id is not None:
                    tags['SPOTIFY_TRACK_ID'] = id
                    tags['SPOTY_FOUND_BY'] = 'ISRC'
                    found.append(tags)
                    bar.update(1)
                    continue

            if "TITLE" in tags and "ARTIST" in tags:
                if not ignore_duration and 'SPOTY_LENGTH' in tags:
                    id = find_track_id_by_artist_and_title(tags['ARTIST'], tags['TITLE'], tags['SPOTY_LENGTH'])
                else:
                    id = find_track_id_by_artist_and_title(tags['ARTIST'], tags['TITLE'])
                if id is not None:
                    tags['SPOTIFY_TRACK_ID'] = id
                    tags['SPOTY_FOUND_BY'] = 'TITLE,ARTIST'
                    found.append(tags)
                    bar.update(1)
                    continue

            not_found.append(tags)
            bar.update(1)

    return found, not_found


def get_playlist(playlist_id: str):
    playlist_id = parse_playlist_id(playlist_id)

    log.info(f'Requesting playlist {playlist_id}')

    try:
        playlist = get_sp().playlist(playlist_id)
        return playlist
    except:
        return None


def get_playlist_with_full_list_of_tracks(playlist_id: str, add_spoty_tags=True, show_progressbar=False):
    playlist_id = parse_playlist_id(playlist_id)

    log.info(f'Collecting playlist {playlist_id}')

    playlist = get_sp().playlist(playlist_id)
    total_tracks = playlist["tracks"]["total"]
    tracks = playlist["tracks"]["items"]

    if add_spoty_tags:
        add_spoty_tags_to_tracks([], tracks, playlist_id, playlist['name'])

    log.debug(f'Playlist {playlist_id} have {total_tracks} tracks (playlist name: "{playlist["name"]}")')
    log.debug(f'Collected {len(tracks)}/{total_tracks} tracks in playlist {playlist_id}')

    # if playlist is larger than 100 songs, continue loading it until end
    result = playlist
    if not show_progressbar:
        while len(tracks) < total_tracks:
            if 'next' in result:
                result = get_sp().next(result)
            else:
                result = get_sp().next(result["tracks"])
            if add_spoty_tags:
                add_spoty_tags_to_tracks(tracks, result['items'], playlist_id, playlist['name'])
            tracks.extend(result['items'])
            log.debug(f'Collected {len(tracks)}/{total_tracks} tracks in playlist {playlist_id}')
    else:
        with click.progressbar(length=total_tracks, label=f'Reading {total_tracks} tracks from playlist '+playlist_id) as bar:
            while len(tracks) < total_tracks:
                if 'next' in result:
                    result = get_sp().next(result)
                else:
                    result = get_sp().next(result["tracks"])
                if add_spoty_tags:
                    add_spoty_tags_to_tracks(tracks, result['items'], playlist_id, playlist['name'])
                tracks.extend(result['items'])
                log.debug(f'Collected {len(tracks)}/{total_tracks} tracks in playlist {playlist_id}')
                bar.update(len(tracks)-bar.pos)
            bar.finish()

    playlist["tracks"]["items"] = tracks

    return playlist


def delete_playlist(playlist_id: str, confirm=False):
    playlist_id = parse_playlist_id(playlist_id)
    playlist = get_playlist(playlist_id)
    if playlist is None:
        return False

    if not confirm:
        if not click.confirm(f'Do you want to delete playlist "{playlist["name"]}" ({playlist["id"]})'):
            click.echo("\nCanceled")
            return False
        click.echo()  # for new line

    get_sp().current_user_unfollow_playlist(playlist_id)

    return True


def get_current_user_id():
    return get_sp().me()['id']


def get_list_of_playlists(only_owned_by_user=True):
    user_id = get_current_user_id()
    playlists = []

    log.info(f'Collecting playlists for current user')

    with click.progressbar(length=100, label='Reading current user spotify playlists') as bar:

        # load first 50 playlists
        result = get_sp().current_user_playlists(limit=50)
        playlists.extend(result['items'])
        total_playlists = result['total']

        log.debug(f'Read {len(playlists)}/{total_playlists} for current user')

        bar.length = total_playlists
        bar.update(len(playlists))

        # load next 50 playlists
        while result['next']:
            result = get_sp().next(result)
            playlists.extend(result['items'])
            bar.update(len(playlists))

            log.debug(f'Read {len(playlists)}/{total_playlists} for current user')

    if only_owned_by_user:
        playlists = list(filter(lambda pl: pl['owner']['id'] == user_id, playlists))

    return playlists


def find_playlist_by_name(name: str, only_owned_by_user=True, playlists=None):
    if playlists is None:
        playlists = get_list_of_playlists(only_owned_by_user)
    return list(filter(lambda pl: pl['name'] == name, playlists))


def get_list_of_user_playlists(user_id: str):
    log.info(f'Collecting playlists for user {user_id}')

    with click.progressbar(length=100, label=f'Reading user {user_id} spotify playlists') as bar:
        # load first 50 playlists
        playlists = []
        result = get_sp().user_playlists(user=user_id, limit=50)
        playlists.extend(result['items'])
        total_playlists = result['total']

        log.debug(f'Collected {len(playlists)}/{total_playlists} playlists for user {user_id}')

        bar.length = total_playlists
        bar.update(len(playlists))

        # load next 50 playlists
        while result['next']:
            result = get_sp().next(result)
            playlists.extend(result['items'])
            bar.update(len(playlists))

            log.debug(f'Collected {len(playlists)}/{total_playlists} playlists for user {user_id}')

        return playlists


def create_playlist(name: str):
    log.info(f'Creating new playlist')

    user_id = get_current_user_id()
    new_playlist = get_sp().user_playlist_create(user_id, name)
    id = new_playlist['id']

    log.success(f'New playlist created (id: {id}, name: "{name}")')

    return id


def copy_playlist(playlist_id: str):
    playlist_id = parse_playlist_id(playlist_id)

    log.info(f'Creating a copy of playlist {playlist_id}')

    playlist = get_playlist_with_full_list_of_tracks(playlist_id)
    tracks = playlist["tracks"]["items"]

    ids = get_track_ids(tracks)
    new_playlist_id = create_playlist(playlist['name'])
    tracks_added, import_duplicates, already_exist = add_tracks_to_playlist_by_ids(new_playlist_id, ids, True)

    log.success(f"Playlist {playlist_id} copy completed ({len(tracks_added)} tracks added).")

    return new_playlist_id, tracks_added


def get_tracks_of_playlist(playlist_id: str, add_spoty_tags=True, playlist_name: str = None):
    playlist_id = parse_playlist_id(playlist_id)

    log.info(f'Collecting tracks from playlist {playlist_id}')

    # load the first 100 songs
    tracks = []
    result = get_sp().playlist_items(playlist_id, additional_types=['track'], limit=100)

    new_tracks = result['items']
    if (add_spoty_tags):
        add_spoty_tags_to_tracks(tracks, new_tracks, playlist_id, playlist_name)
    tracks.extend(new_tracks)

    log.debug(f'Collected {len(tracks)}/{result["total"]} tracks')

    # if playlist is larger than 100 songs, continue loading it until end
    while result['next']:
        result = get_sp().next(result)

        new_tracks = result['items']
        if (add_spoty_tags):
            add_spoty_tags_to_tracks(tracks, new_tracks, playlist_id, playlist_name)
        tracks.extend(new_tracks)

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


def add_spoty_tags_to_tracks(tracks: list, new_tracks: list, playlist_id: str, playlist_name: str):
    counter = len(tracks)
    for track in new_tracks:
        track['track']['SPOTY_PLAYLIST_ID'] = playlist_id
        track['track']['SPOTY_PLAYLIST_INDEX'] = str(counter + 1)
        track['track']['SPOTY_SOURCE'] = 'SPOTIFY'
        if playlist_name is not None:
            track['track']['SPOTY_PLAYLIST_NAME'] = playlist_name
        try:
            track['track']['SPOTY_TRACK_ID'] = track['track']['id']
        except:
            pass
        counter += 1
    return counter


def add_tracks_to_playlist_by_tags(playlist_id: str, tags_list: list, allow_duplicates=False):
    playlist_id = parse_playlist_id(playlist_id)

    tags_list = tags_list.copy()

    for i in range(len(tags_list)):
        tags_list[i]['SPOTIFY_TRACK_ID'] = parse_track_id(tags_list[i]['SPOTIFY_TRACK_ID'])

    import_duplicates = []

    if not allow_duplicates:
        tags_list, import_duplicates = spoty.utils.remove_duplicated_tags(tags_list, ['SPOTIFY_TRACK_ID'])
        if len(import_duplicates) > 0:
            log.debug(f'{len(import_duplicates)} duplicates found when adding tracks. It will be skipped.')

    log.info(f'Adding {len(tags_list)} tracks to playlist {playlist_id}')

    already_exist = []

    if not allow_duplicates:
        tracks = get_tracks_of_playlist(playlist_id)
        tags_in_playlist = read_tags_from_spotify_tracks(tracks)
        tags_list, already_exist = spoty.utils.remove_exist_tags(tags_in_playlist, tags_list, ['SPOTIFY_TRACK_ID'])
        if len(already_exist) > 0:
            log.debug(f'{len(already_exist)} tracks already exist and will be skipped.')

    track_ids = get_track_ids_from_tags_list(tags_list)

    i = 0
    next_tracks = []
    while i < len(track_ids):
        next_tracks.append(track_ids[i])
        if len(next_tracks) == 100 or i == len(track_ids) - 1:
            get_sp().playlist_add_items(playlist_id, next_tracks)
            log.debug(f'{len(next_tracks)} tracks added to playlist')
            next_tracks = []
        i += 1

    log.success(f'Adding tracks to playlist {playlist_id} complete (tracks added: {len(tags_list)}')

    return tags_list, import_duplicates, already_exist


def add_tracks_to_playlist_by_ids(playlist_id: str, track_ids: list, allow_duplicates=False):
    playlist_id = parse_playlist_id(playlist_id)

    for i in range(len(track_ids)):
        track_ids[i] = parse_track_id(track_ids[i])

    import_duplicates = []

    if not allow_duplicates:
        track_ids, import_duplicates = spoty.utils.remove_duplicates(track_ids)
        if len(import_duplicates) > 0:
            log.debug(f'{len(import_duplicates)} duplicates found when adding tracks. It will be skipped.')

    log.info(f'Adding {len(track_ids)} tracks to playlist {playlist_id}')

    already_exist = []

    if not allow_duplicates:
        tracks = get_tracks_of_playlist(playlist_id)
        ids_in_playlist = get_track_ids(tracks)
        track_ids, already_exist = spoty.utils.remove_exist(ids_in_playlist, track_ids)
        if len(already_exist) > 0:
            log.debug(f'{len(already_exist)} tracks already exist and will be skipped.')

    tracks_added = []

    i = 0
    next_tracks = []
    while i < len(track_ids):
        next_tracks.append(track_ids[i])
        if len(next_tracks) == 100 or i == len(track_ids) - 1:
            get_sp().playlist_add_items(playlist_id, next_tracks)
            tracks_added.extend(next_tracks)
            log.debug(f'{len(next_tracks)} tracks added to playlist')
            next_tracks = []
        i += 1

    log.success(f'Adding tracks to playlist {playlist_id} complete (tracks added: {len(next_tracks)}')

    return tracks_added, import_duplicates, already_exist


def remove_all_tracks_from_playlist(playlist_id: str, confirm=False):
    playlist_id = parse_playlist_id(playlist_id)
    tracks = get_tracks_of_playlist(playlist_id)

    if len(tracks) == 0:
        return False

    if not confirm:
        if not click.confirm(f'Do you want to remove all tracks from playlist {playlist_id}?'):
            click.echo("\nCanceled")
            return False
        click.echo()  # for new line

    ids = get_track_ids(tracks)
    remove_tracks_from_playlist(playlist_id, ids)
    return True


def get_missing_tracks_from_playlist(playlist_id: str, track_ids: list, confirm=False):
    playlist_id = parse_playlist_id(playlist_id)
    tracks = get_tracks_of_playlist(playlist_id)

    if len(tracks) == 0:
        return []

    missing_tracks = []
    for track in tracks:
        if track['track']['id'] not in track_ids:
            missing_tracks.append(track)

    return missing_tracks


def remove_tracks_from_playlist(playlist_id: str, track_ids: list):
    playlist_id = parse_playlist_id(playlist_id)

    log.info(f'Removing {len(track_ids)} tracks from playlist {playlist_id}')

    i = 0
    next_tracks = []
    while i < len(track_ids):
        track_ids[i] = parse_track_id(track_ids[i])
        next_tracks.append(track_ids[i])
        if len(next_tracks) == 100 or i == len(track_ids) - 1:
            snapshot = get_sp().playlist_remove_all_occurrences_of_items(playlist_id, next_tracks)
            next_tracks = []
        i += 1

    log.success(f'Tracks removed from playlist {playlist_id}')


def remove_liked_tracks_in_playlist(playlist_id: str):
    playlist_id = parse_playlist_id(playlist_id)

    log.info(f'Removing liked tracks from playlist {playlist_id}')

    tracks = get_tracks_of_playlist(playlist_id)
    ids = get_track_ids(tracks)
    liked_track_ids = get_liked_track_ids(ids)
    remove_tracks_from_playlist(playlist_id, liked_track_ids)

    log.success(f'{len(liked_track_ids)} liked tracks removed from playlist {playlist_id}.')

    return liked_track_ids


def get_invalid_tracks_in_playlist(playlist_id: str):
    playlist_id = parse_playlist_id(playlist_id)

    log.info(f'Listing invalid tracks in playlist {playlist_id}')

    invalid_tracks = []

    tracks = get_tracks_of_playlist(playlist_id)
    for track in tracks:
        try:
            id = track['track']['id']
            assert id is not None, "Track id is None"
        except:
            invalid_tracks.append(track)

    return invalid_tracks


def import_playlists_from_tags_list(tags_list: list, grouping_pattern: str, overwrite_if_exist=False,
                                    append_if_exist=False,
                                    allow_duplicates=True, confirm=False):
    grouped_tags = spoty.utils.group_tags_by_pattern(tags_list, grouping_pattern)
    all_playlist_ids, all_added, all_source_duplicates, all_already_exist = \
        import_playlists_from_tag_groups(grouped_tags, overwrite_if_exist, append_if_exist, allow_duplicates, confirm)

    return all_playlist_ids, all_added, all_source_duplicates, all_already_exist


def import_playlists_from_tag_groups(grouped_tags: dict, overwrite_if_exist=False,
                                     append_if_exist=False,
                                     allow_duplicates=True, confirm=False):
    all_playlist_ids = []
    all_added = []
    all_source_duplicates = []
    all_already_exist = []

    playlists = None
    if append_if_exist or overwrite_if_exist:
        playlists = get_list_of_playlists(True)

    with click.progressbar(grouped_tags.items(), label=f'Importing {len(grouped_tags)} playlists') as bar:
        for group_name, g_tags_list in bar:
            playlist_id, added, source_duplicates, already_exist \
                = import_playlist_from_tags_list(group_name, g_tags_list, overwrite_if_exist, append_if_exist,
                                                 allow_duplicates, confirm, playlists)

            all_playlist_ids.append(playlist_id)
            all_added.extend(added)
            all_source_duplicates.extend(source_duplicates)
            all_already_exist.extend(already_exist)

    return all_playlist_ids, all_added, all_source_duplicates, all_already_exist


def import_playlist_from_tags_list(playlist_name: str, tags_list: list, overwrite_if_exist=False, append_if_exist=False,
                                   allow_duplicates=True, confirm=False, playlists=None):
    if len(tags_list) == 0:
        return [], [], [], []

    log.info(f'Importing playlist "{playlist_name}"')

    playlist_id = None

    if overwrite_if_exist or append_if_exist:
        found_playlists = find_playlist_by_name(playlist_name, True, playlists)

        if len(found_playlists) > 0:
            if append_if_exist:
                if len(found_playlists) > 1:
                    if confirm:
                        click.echo(
                            f'\n{len(found_playlists)} playlists with name "{playlist_name}" found in Spotify library. Choosing the first one.')
                    else:
                        if not click.confirm(
                                f'\n{len(found_playlists)} playlists with name "{playlist_name}" found in Spotify library. Choose the first one?'):
                            click.echo("\nCanceled")
                            log.info(f'Canceled by user (more than one playlists found with name "{playlist_name})"')
                            return [], [], [], []
                        click.echo()  # for new line
            if overwrite_if_exist:
                if len(found_playlists) > 1:
                    if confirm:
                        click.echo(
                            f'\n{len(found_playlists)} playlists with name "{playlist_name}" found in Spotify library. Choosing the first one..')
                    else:
                        if not click.confirm(
                                f'\n{len(found_playlists)} playlists with name "{playlist_name}" found in Spotify library. Choose the first one?'):
                            click.echo("\nCanceled")
                            log.info(f'Canceled by user (more than one playlists found with name "{playlist_name})"')
                            return [], [], [], []
                        click.echo()  # for new line

                new_ids = get_track_ids_from_tags_list(tags_list)
                missing_tracks = get_missing_tracks_from_playlist(found_playlists[0]['id'], new_ids, True)
                if len(missing_tracks) > 0:
                    if not confirm:
                        if not click.confirm(
                                f'\nDo you want to remove {len(missing_tracks)} tracks from playlist "{playlist_name}" (these tracks are not in the provided new track list)?'):
                            click.echo("\nCanceled")
                            return [], [], [], []
                        click.echo()  # for new line

                    ids = get_track_ids(missing_tracks)
                    remove_tracks_from_playlist(found_playlists[0]['id'], ids)

            playlist_id = found_playlists[0]['id']

    if playlist_id is None:
        playlist_id = create_playlist(playlist_name)

    added, source_duplicates, already_exist = add_tracks_to_playlist_by_tags(playlist_id, tags_list, allow_duplicates)

    log.success(f'Playlist imported (new tracks: "{len(added)}")  id: {playlist_id} name: "{playlist_name}"')

    return playlist_id, added, source_duplicates, already_exist


def like_all_tracks_in_playlist(playlist_id: str):
    playlist_id = parse_playlist_id(playlist_id)

    log.info(f'Adding likes to all tracks in playlist {playlist_id}')

    tracks = get_tracks_of_playlist(playlist_id)
    ids = get_track_ids(tracks)
    not_liked_track_ids = get_not_liked_track_ids(ids)
    add_tracks_to_liked(not_liked_track_ids)

    log.success(f'{len(not_liked_track_ids)} tracks added to liked tracks in playlist {playlist_id}.')

    return not_liked_track_ids


def get_liked_tracks_count():
    results = get_sp().current_user_saved_tracks(limit=50)
    total_likes_count = results['total']
    return total_likes_count


def get_liked_tracks():
    tracks = []

    log.info(f'Collecting liked tracks')

    with click.progressbar(length=100, label='Collecting liked tracks') as bar:
        results = get_sp().current_user_saved_tracks(limit=50)
        total_likes_count = results['total']
        tracks.extend(results['items'])

        bar.length = total_likes_count
        bar.update(len(tracks))

        log.debug(f'Collected {len(tracks)}/{total_likes_count}')

        while results['next']:
            results = get_sp().next(results)
            tracks.extend(results['items'])
            bar.update(len(tracks))

            log.debug(f'Collected {len(tracks)}/{total_likes_count}')

    return tracks


def add_tracks_to_liked(track_ids: list, show_progress_bar=False):
    for i in range(len(track_ids)):
        track_ids[i] = parse_track_id(track_ids[i])

    log.info(f'Adding {len(track_ids)} to saved tracks')

    i = 0
    next_tracks = []

    if not show_progress_bar:
        while i < len(track_ids):
            next_tracks.append(track_ids[i])
            if len(next_tracks) == 50 or i == len(track_ids) - 1:
                get_sp().current_user_saved_tracks_add(tracks=next_tracks)
                log.debug(f'Added {i + 1}/{len(next_tracks)} tracks to saved')
                next_tracks = []
            i += 1
    else:
        with click.progressbar(length=len(track_ids), label=f'Adding {len(track_ids)} liked tracks') as bar:
            while i < len(track_ids):
                next_tracks.append(track_ids[i])
                if len(next_tracks) == 50 or i == len(track_ids) - 1:
                    get_sp().current_user_saved_tracks_add(tracks=next_tracks)
                    log.debug(f'Added {i + 1}/{len(next_tracks)} tracks to saved')
                    bar.update(len(next_tracks))
                    next_tracks = []
                i += 1


def remove_tracks_from_liked(track_ids: list, show_progress_bar=False):
    for i in range(len(track_ids)):
        track_ids[i] = parse_track_id(track_ids[i])

    log.info(f'Adding {len(track_ids)} to saved tracks')

    i = 0
    next_tracks = []

    if not show_progress_bar:
        while i < len(track_ids):
            next_tracks.append(track_ids[i])
            if len(next_tracks) == 50 or i == len(track_ids) - 1:
                get_sp().current_user_saved_tracks_delete(tracks=next_tracks)
                log.debug(f'Removed {i + 1}/{len(next_tracks)} tracks from saved')
                next_tracks = []
            i += 1
    else:
        with click.progressbar(length=len(track_ids), label='Adding liked tracks') as bar:
            while i < len(track_ids):
                next_tracks.append(track_ids[i])
                if len(next_tracks) == 50 or i == len(track_ids) - 1:
                    get_sp().current_user_saved_tracks_delete(tracks=next_tracks)
                    log.debug(f'Removed {i + 1}/{len(next_tracks)} tracks from saved')
                    bar.update(len(next_tracks))
                    next_tracks = []
                i += 1


def export_liked_tracks_to_file(file_name: str):
    log.info(f'Exporting liked tracks from file "{file_name}"')

    liked_tracks = get_liked_tracks()
    tag_tracks = read_tags_from_spotify_tracks(liked_tracks)
    spoty.csv_playlist.write_tags_to_csv(tag_tracks, file_name)

    log.success(f'{len(liked_tracks)} liked tracks exported to file: "{file_name}"')

    return liked_tracks


def import_likes_from_file(file_name: str, invert=False, show_progressbar=False):
    log.info(f'Importing liked tracks from file "{file_name}"')
    tags_list = spoty.csv_playlist.read_tags_from_csv(file_name)
    ids = spoty.spotify_api.get_track_ids_from_tags_list(tags_list)

    # remove already exist
    if not invert:
        ids = get_not_liked_track_ids(ids, show_progressbar)
    else:
        ids = get_liked_track_ids(ids, show_progressbar)

    if len(ids) > 0:
        if not invert:
            add_tracks_to_liked(ids, show_progressbar)
        else:
            remove_tracks_from_liked(ids, show_progressbar)

    log.success(f'{len(tags_list)} liked tracks imported from file: "{file_name}"')

    return tags_list


def get_likes_for_tracks(track_ids: list, show_progressbar=False):
    likes = []

    i = 0
    next_tracks = []

    if not show_progressbar:
        while i < len(track_ids):
            next_tracks.append(track_ids[i])
            if len(next_tracks) == 50 or i == len(track_ids) - 1:
                likes_new = get_sp().current_user_saved_tracks_contains(tracks=next_tracks)
                likes.extend(likes_new)
                next_tracks = []
            i += 1
    else:
        with click.progressbar(length=len(track_ids), label='Collecting liked tracks') as bar:
            while i < len(track_ids):
                next_tracks.append(track_ids[i])
                if len(next_tracks) == 50 or i == len(track_ids) - 1:
                    likes_new = get_sp().current_user_saved_tracks_contains(tracks=next_tracks)
                    likes.extend(likes_new)
                    bar.update(len(next_tracks))
                    next_tracks = []
                i += 1

    return likes


def get_liked_track_ids(track_ids: list, show_progressbar=False):
    liked_tracks = []

    likes = get_likes_for_tracks(track_ids, show_progressbar)
    for i in range(len(track_ids)):
        if likes[i]:
            liked_tracks.append(track_ids[i])

    return liked_tracks


def get_not_liked_track_ids(track_ids: list, show_progressbar=False):
    not_liked_tracks = []

    likes = get_likes_for_tracks(track_ids, show_progressbar)
    for i in range(len(track_ids)):
        if not likes[i]:
            not_liked_tracks.append(track_ids[i])

    return not_liked_tracks


def get_liked_tags_list(new_sub_tags_list, show_progressbar=False):
    liked_tags_list = []
    not_liked_tags_list = []
    track_ids = get_track_ids_from_tags_list(new_sub_tags_list)
    likes = get_likes_for_tracks(track_ids, show_progressbar)
    for i in range(len(track_ids)):
        if likes[i]:
            liked_tags_list.append(new_sub_tags_list[i])
        else:
            not_liked_tags_list.append(new_sub_tags_list[i])

    return liked_tags_list, not_liked_tags_list


def get_track_artist_and_title(track: dict):
    artists = list(map(lambda artist: artist['name'], track['artists']))
    artists_str = ', '.join(artists)
    artists_str.replace(' - ', ' ')
    title = track['name'].replace(' - ', ' ')
    return f"{artists_str} - {title}"


def get_track_ids(tracks: list):
    if len(tracks) == 0:
        return []
    else:
        return [item['track']['id'] for item in tracks]


def get_track_ids_from_tags_list(tags_list):
    if len(tags_list) == 0:
        return []
    else:
        return [str(track['SPOTIFY_TRACK_ID']) for track in tags_list]


def get_playlists_ids(playlists: list):
    if len(playlists) == 0:
        return []
    else:
        return [item['id'] for item in playlists]


def parse_playlist_id(id_or_uri: str):
    if id_or_uri.startswith("https://open.spotify.com/playlist/"):
        id_or_uri = id_or_uri.split('/playlist/')[1]
        id_or_uri = id_or_uri.split('?')[0]
    return id_or_uri


def parse_track_id(id_or_uri: str):
    if id_or_uri.startswith("https://open.spotify.com/track/"):
        id_or_uri = id_or_uri.split('/track/')[1]
        id_or_uri = id_or_uri.split('?')[0]
    return id_or_uri


def parse_user_id(id_or_uri: str):
    if id_or_uri.startswith("https://open.spotify.com/user/"):
        id_or_uri = id_or_uri.split('/user/')[1]
        id_or_uri = id_or_uri.split('?')[0]
    return id_or_uri


def read_tags_from_spotify_tracks(tracks: list):
    tag_tracks = []

    for track in tracks:
        tags = read_tags_from_spotify_track(track)
        tag_tracks.append(tags)

    return tag_tracks


def read_tags_from_spotify_track(track: dict):
    date_added = track['added_at'] if "added_at" in track else None

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

    tags['SPOTY_LENGTH'] = str(int(int(track['duration_ms']) / 1000))

    try:
        tags['SPOTIFY_ALBUM_ID'] = track['album']['id']
    except:
        pass

    try:
        tags['WWWAUDIOFILE'] = track['external_urls']['spotify']
    except:
        pass

    tags['SPOTIFY_TRACK_ID'] = track["id"]

    tags['EXPLICIT'] = track['explicit']

    tags['TRACK'] = track['track_number']

    try:
        tags['YEAR'] = track['album']['release_date']
    except:
        pass

    # tags['SPOTIFY_DATE_ADDED'] = date_added
    if date_added is not None:
        timestamp = datetime.datetime.strptime(date_added, "%Y-%m-%dT%H:%M:%SZ")  # format: 2021-12-19T19:35:17Z
        tags['SPOTY_TRACK_ADDED'] = timestamp.strftime('%Y-%m-%d %H:%M:%S')

    for tag in spoty.utils.spoty_tags:
        if tag in track:
            tags[tag] = track[tag]

    tags = spoty.utils.clean_tags_after_read(tags)

    return tags
