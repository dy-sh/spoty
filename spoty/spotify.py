from spoty import sp
from spoty import log
import spoty.utils
import spoty.csv_playlist
import os.path
import click
import time
import re




def get_tracks_from_playlists(playlist_ids):
    all_tracks = []
    all_tags_list = []
    all_received_playlists = []

    requested_playlists = []

    with click.progressbar(playlist_ids, label=f'Reading tracks in {len(playlist_ids)} spotify playlists') as bar:
        for playlist_id in bar:

            # remove already requested playlists
            if playlist_id in requested_playlists:
                click.echo(f'Spotify playlist {playlist_id} requested twice. In will be skipped.')
                continue

            playlist=get_playlist_with_full_list_of_tracks(playlist_ids)
            requested_playlists.append(playlist_id)

            tracks = playlist.tracks
            for track in tracks:
                track['track']['SPOTY_PLAYLIST_NAME'] = playlist['name']
                track['track']['SPOTY_PLAYLIST_ID'] = playlist['id']

            tags = read_tags_from_spotify_tracks(tracks)

            all_tracks.extend(tracks)
            all_tags_list.extend(tags)
            all_received_playlists.append(playlist_id)

    return all_tracks, all_tags_list, all_received_playlists


def get_tracks_of_spotify_users(user_ids, playlists_names_regex=None):
    if playlists_names_regex == None:
        playlists_names_regex = []

    all_tracks = []
    all_tags_list = []
    all_playlists = []

    for user_id in user_ids:
        user_id = parse_user_id(user_id)
        if user_id == 'me':
            playlists = get_list_of_playlists()
            click.echo(f'You have {len(playlists)} playlists in Spotify library')
        else:
            playlists = get_list_of_user_playlists(user_id)
            click.echo(f'User {user_id} has {len(playlists)} playlists in Spotify library')

        if len(playlists_names_regex) > 0:
            playlists = list(filter(lambda pl: re.findall(playlists_names_regex, pl['name']), playlists))

        # remove already requested playlists
        new_playlists = playlists.copy()
        for pl in playlists:
            if pl in all_playlists:
                click.echo(f'Spotify playlist {pl["id"]} ({pl["name"]}) requested twice. In will be skipped.')
                new_playlists.remove(pl)
        playlists = new_playlists
        if len(playlists) == 0:
            continue

        all_playlists.extend(playlists)

        tracks, tags, playlists = get_tracks_from_playlists(playlists)
        all_tracks.extend(tracks)
        all_tags_list.extend(tags)

    return all_tracks, all_tags_list, all_playlists


def find_track_by_query(query):
    res = sp.search(query)

    try:
        # todo: find for the best matching by album, length and other tags
        tracks = res['tracks']['items']
        return tracks
    except:
        pass

    return []


def find_track_by_isrc(isrc):
    res = sp.search(f'isrc:{isrc}')

    try:
        # todo: find for the best matching by album, length and other tags
        track = res['tracks']['items'][0]
        return track
    except:
        pass

    return None


def find_track_id_by_isrc(isrc):
    track = find_track_by_isrc(isrc)
    return track['id'] if track is not None else None


def find_track_by_artist_and_title(artist, title):
    res = sp.search(f'track:{title} artist:{artist}')

    try:
        # todo: find for the best matching by album, length and other tags
        track = res['tracks']['items'][0]
        return track
    except:
        pass

    return None


def find_track_id_by_artist_and_title(artist, title):
    track = find_track_by_artist_and_title(artist, title)
    return track['id'] if track is not None else None


def find_tracks_from_tags(tags_list):
    found_ids = []
    not_found_tracks = []

    for tags in tags_list:
        if "SPOTIFY_TRACK_ID" in tags:
            found_ids.append(tags['SPOTIFY_TRACK_ID'])
            continue

        if "ISRC" in tags:
            id = find_track_id_by_isrc(tags['ISRC'])
            if id is not None:
                found_ids.append(id)
                continue

        if "TITLE" in tags and "ARTIST" in tags:
            id = find_track_id_by_artist_and_title(tags['ARTIST'], tags['TITLE'])
            if id is not None:
                found_ids.append(id)
                continue

        not_found_tracks.append(tags)

    return found_ids, not_found_tracks


def get_playlist(playlist_id):
    playlist_id = parse_playlist_id(playlist_id)

    log.info(f'Requesting playlist {playlist_id}')

    playlist = sp.playlist(playlist_id)

    return playlist


def get_playlist_with_full_list_of_tracks(playlist_id):
    playlist_id = parse_playlist_id(playlist_id)

    log.info(f'Collecting playlist {playlist_id}')

    playlist = sp.playlist(playlist_id)
    total_tracks = playlist["tracks"]["total"]
    tracks = playlist["tracks"]["items"]

    log.debug(f'Playlist {playlist_id} have {total_tracks} tracks (playlist name: "{playlist["name"]}")')
    log.debug(f'Collected {len(tracks)}/{total_tracks} tracks in playlist {playlist_id}')

    # if playlist is larger than 100 songs, continue loading it until end
    result = playlist
    while len(tracks) < total_tracks:
        if 'next' in result:
            result = sp.next(result)
        else:
            result = sp.next(result["tracks"])
        tracks.extend(result['items'])
        log.debug(f'Collected {len(tracks)}/{total_tracks} tracks in playlist {playlist_id}')

    playlist["tracks"]["items"] = tracks

    return playlist


def delete_playlist(playlist_id, confirm=False):
    playlist = get_playlist(playlist_id)
    if playlist is None:
        return False

    if not confirm:
        if not click.confirm(f'Do you want to delete playlist {playlist["id"]} ("{playlist["name"]}")'):
            click.echo("\nCanceled")
            return False
        click.echo()  # for new line

    sp.current_user_unfollow_playlist(playlist_id)

    return True


def get_list_of_playlists(only_owned_by_user=True):
    user_id = sp.me()['id']
    playlists = []

    log.info(f'Collecting playlists for current user')

    with click.progressbar(length=100, label='Reading current user spotify playlists') as bar:

        # load first 50 playlists
        result = sp.current_user_playlists(limit=50)
        playlists.extend(result['items'])
        total_playlists = result['total']

        log.debug(f'Read {len(playlists)}/{total_playlists} for current user')

        bar.length = total_playlists
        bar.update(len(playlists))

        # load next 50 playlists
        while result['next']:
            result = sp.next(result)
            playlists.extend(result['items'])
            bar.update(len(playlists))

            log.debug(f'Read {len(playlists)}/{total_playlists} for current user')

    if (only_owned_by_user):
        playlists = list(filter(lambda pl: pl['owner']['id'] == user_id, playlists))

    return playlists


def find_playlist_by_name(name, only_owned_by_user=True):
    playlists = get_list_of_playlists(only_owned_by_user)
    return list(filter(lambda pl: pl['name'] == name, playlists))


def get_list_of_user_playlists(user_id: str):
    log.info(f'Collecting playlists for user {user_id}')

    with click.progressbar(length=100, label=f'Reading user {user_id} spotify playlists') as bar:
        # load first 50 playlists
        playlists = []
        result = sp.user_playlists(user=user_id, limit=50)
        playlists.extend(result['items'])
        total_playlists = result['total']

        log.debug(f'Collected {len(playlists)}/{total_playlists} playlists for user {user_id}')

        bar.length = total_playlists
        bar.update(len(playlists))

        # load next 50 playlists
        while result['next']:
            result = sp.next(result)
            playlists.extend(result['items'])
            bar.update(len(playlists))

            log.debug(f'Collected {len(playlists)}/{total_playlists} playlists for user {user_id}')

        return playlists


def create_playlist(name):
    log.info(f'Creating new playlist')

    user_id = sp.me()['id']
    new_playlist = sp.user_playlist_create(user_id, name)
    id = new_playlist['id']

    log.success(f'New playlist created (id: {id}, name: "{name}")')

    return id


def copy_playlist(playlist_id):
    playlist_id = parse_playlist_id(playlist_id)

    log.info(f'Creating a copy of playlist {playlist_id}')

    playlist = get_playlist_with_full_list_of_tracks(playlist_id)
    tracks = playlist["tracks"]["items"]

    ids = get_track_ids(tracks)
    new_playlist_id = create_playlist(playlist['name'])
    tracks_added, import_duplicates, already_exist = add_tracks_to_playlist(new_playlist_id, ids, True)

    log.success(f"Playlist {playlist_id} copy completed ({len(tracks_added)} tracks added).")

    return new_playlist_id, tracks_added


def get_tracks_of_playlist(playlist_id, add_playlist_info=True):
    playlist_id = parse_playlist_id(playlist_id)

    log.info(f'Collecting tracks from playlist {playlist_id}')

    # load the first 100 songs
    tracks = []
    result = sp.playlist_items(playlist_id, additional_types=['track'], limit=100)

    i = 0
    new_tracks = result['items']
    if (add_playlist_info):
        for track in new_tracks:
            track['track']['SPOTY_PLAYLIST_ID'] = playlist_id
            track['track']['SPOTY_PLAYLIST_INDEX'] = i + 1
            track['track']['SPOTY_PLAYLIST_SOURCE'] = 'SPOTIFY'
            try:
                track['track']['SPOTY_TRACK_ID'] = track['track']['id']
            except:
                pass
            i += 1

    tracks.extend(new_tracks)

    log.debug(f'Collected {len(tracks)}/{result["total"]} tracks')

    # if playlist is larger than 100 songs, continue loading it until end
    while result['next']:
        result = sp.next(result)

        new_tracks = result['items']
        if (add_playlist_info):
            for track in new_tracks:
                track['track']['SPOTY_PLAYLIST_ID'] = playlist_id
                track['track']['SPOTY_PLAYLIST_INDEX'] = i + 1
                track['track']['SPOTY_PLAYLIST_SOURCE'] = 'SPOTIFY'
                try:
                    track['track']['SPOTY_TRACK_ID'] = track['track']['id']
                except:
                    pass
                i += 1

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


def add_tracks_to_playlist(playlist_id, track_ids, allow_duplicates=False):
    playlist_id = parse_playlist_id(playlist_id)

    import_duplicates = []

    if not allow_duplicates:
        track_ids, import_duplicates = spoty.utils.remove_duplicates(track_ids)
        if len(import_duplicates) > 0:
            log.debug(f'{len(import_duplicates)} duplicates found when adding tracks. It will be skipped.')

    for i in range(len(track_ids)):
        track_ids[i] = parse_track_id(track_ids[i])

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
            sp.playlist_add_items(playlist_id, next_tracks)
            tracks_added.extend(next_tracks)
            log.debug(f'{len(next_tracks)} tracks added to playlist')
            next_tracks = []
        i += 1

    log.success(f'Adding tracks to playlist {playlist_id} complete (tracks added: {len(next_tracks)}')

    return tracks_added, import_duplicates, already_exist


def remove_all_tracks_from_playlist(playlist_id, confirm=False):
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


def remove_tracks_from_playlist(playlist_id, track_ids):
    playlist_id = parse_playlist_id(playlist_id)

    log.info(f'Removing {len(track_ids)} tracks from playlist {playlist_id}')

    i = 0
    next_tracks = []
    while i < len(track_ids):
        track_ids[i] = parse_track_id(track_ids[i])
        next_tracks.append(track_ids[i])
        if len(next_tracks) == 100 or i == len(track_ids) - 1:
            snapshot = sp.playlist_remove_all_occurrences_of_items(playlist_id, next_tracks)
            next_tracks = []
        i += 1

    log.success(f'Tracks removed from playlist {playlist_id}')


def remove_liked_tracks_in_playlist(playlist_id):
    playlist_id = parse_playlist_id(playlist_id)

    log.info(f'Removing liked tracks from playlist {playlist_id}')

    tracks = get_tracks_of_playlist(playlist_id)
    ids = get_track_ids(tracks)
    liked_track_ids = get_liked_track_ids(ids)
    remove_tracks_from_playlist(playlist_id, liked_track_ids)

    log.success(f'{len(liked_track_ids)} liked tracks removed from playlist {playlist_id}.')

    return liked_track_ids


def get_invalid_tracks_in_playlist(playlist_id):
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


def export_playlist_to_file(playlist_id, path, overwrite=False, avoid_filenames=None):
    if avoid_filenames is None:
        avoid_filenames = []
    playlist_id = parse_playlist_id(playlist_id)

    log.info(f'Exporting playlist {playlist_id}')

    playlist = get_playlist_with_full_list_of_tracks(playlist_id)

    file_name = get_playlist_file_name(playlist["name"], playlist_id, path, avoid_filenames)

    if os.path.isfile(file_name) and not overwrite:
        time.sleep(0.2)  # waiting progressbar updating
        if not click.confirm(f'\nFile "{file_name}" already exist. Overwrite?'):
            click.echo("\nCanceled")
            log.info(f'Canceled by user (file already exist)')
            return None
        click.echo()  # for new line

    tracks = playlist["tracks"]["items"]

    tag_tracks = read_tags_from_spotify_tracks(tracks)
    spoty.csv_playlist.write_tags_to_csv(tag_tracks, file_name)

    log.success(f'Playlist {playlist_id} exported (file: "{file_name}")')

    return file_name


def import_playlists_from_tags_list(tags_list, grouping_pattern, overwrite_if_exist=False, append_if_exist=False,
                                    allow_duplicates=True, confirm=False):
    all_playlist_ids = []
    all_tracks_added = []
    all_import_duplicates = []
    all_already_exist = []
    all_not_found = []
    grouped_tags = spoty.utils.group_tags_by_pattern(tags_list, grouping_pattern)

    for group_name, g_tags_list in grouped_tags.items():
        playlist_id, tracks_added, import_duplicates, already_exist, not_found \
            = import_playlist_from_tags_list(group_name, g_tags_list, overwrite_if_exist, append_if_exist,
                                             allow_duplicates, confirm)

        all_playlist_ids.append(playlist_id)
        all_tracks_added.extend(tracks_added)
        all_import_duplicates.extend(import_duplicates)
        all_already_exist.extend(already_exist)
        all_not_found.extend(not_found)

    return all_playlist_ids, all_tracks_added, all_import_duplicates, all_already_exist, all_not_found


def import_playlist_from_tags_list(playlist_name, tags_list, overwrite_if_exist=False, append_if_exist=False,
                                   allow_duplicates=True, confirm=False):
    log.info(f'Importing playlist "{playlist_name}"')
    tracks_added = []

    playlist_id = None

    if overwrite_if_exist or append_if_exist:
        found_playlists = find_playlist_by_name(playlist_name)

        if len(found_playlists) > 0:
            if append_if_exist:
                if len(found_playlists) > 1:
                    if confirm:
                        click.echo(
                            f'\n{len(found_playlists)} playlists with name "{playlist_name}" found in Spotify library. Choosing the first one and appending it.')
                    else:
                        if not click.confirm(
                                f'\n{len(found_playlists)} playlists with name "{playlist_name}" found in Spotify library. Choose the first one and append it?'):
                            click.echo("\nCanceled")
                            log.info(f'Canceled by user (more than one playlists found with name "{playlist_name})"')
                            return [], [], [], []
                        click.echo()  # for new line
            if overwrite_if_exist:
                if len(found_playlists) > 1:
                    if confirm:
                        click.echo(
                            f'\n{len(found_playlists)} playlists with name "{playlist_name}" found in Spotify library. Choosing the first one and overwriting it.')
                    else:
                        if not click.confirm(
                                f'\n{len(found_playlists)} playlists with name "{playlist_name}" found in Spotify library. Choose the first one and overwrite it?'):
                            click.echo("\nCanceled")
                            log.info(f'Canceled by user (more than one playlists found with name "{playlist_name})"')
                            return [], [], [], []
                        click.echo()  # for new line
                else:
                    if confirm:
                        click.echo(f'\nPlaylist "{playlist_name}" exist in Spotify library. Overwriting it.')
                    else:
                        if not click.confirm(
                                f'\nPlaylist "{playlist_name}" exist in Spotify library. Overwrite it?'):
                            click.echo("\nCanceled")
                            log.info(f'Canceled by user (playlist found with name "{playlist_name})"')
                            return [], [], [], []
                        click.echo()  # for new line

                remove_all_tracks_from_playlist(found_playlists[0]['id'], True)

            playlist_id = found_playlists[0]['id']

    if playlist_id is None:
        playlist_id = create_playlist(playlist_name)

    found_ids, tracks_not_found = find_tracks_from_tags(tags_list)

    import_duplicates = []
    already_exist = []

    if len(found_ids) > 0:
        tracks_added, import_duplicates, already_exist = add_tracks_to_playlist(playlist_id, found_ids,
                                                                                allow_duplicates)
    log.success(f'Playlist imported (new tracks: "{len(tracks_added)}")  id: {playlist_id} name: "{playlist_name}"')

    return playlist_id, tracks_added, import_duplicates, already_exist, tracks_not_found


def like_all_tracks_in_playlist(playlist_id):
    playlist_id = parse_playlist_id(playlist_id)

    log.info(f'Adding likes to all tracks in playlist {playlist_id}')

    tracks = get_tracks_of_playlist(playlist_id)
    ids = get_track_ids(tracks)
    not_liked_track_ids = get_not_liked_track_ids(ids)
    add_tracks_to_liked(not_liked_track_ids)

    log.success(f'{len(not_liked_track_ids)} tracks added to liked tracks in playlist {playlist_id}.')

    return not_liked_track_ids


def get_tags_from_spotify_library(filter_names, user_id):
    if user_id == None:
        playlists = get_list_of_playlists()
        click.echo(f'You have {len(playlists)} playlists')
    else:
        playlists = get_list_of_user_playlists(user_id)
        click.echo(f'User has {len(playlists)} playlists')

    if len(playlists) == 0:
        exit()

    if filter_names is not None:
        playlists = list(filter(lambda pl: re.findall(filter_names, pl['name']), playlists))
        click.echo(f'{len(playlists)} playlists matches the filter')

    if len(playlists) == 0:
        exit()

    all_tracks_tags = []
    with click.progressbar(playlists, label='Reading tracks from Spotify library') as bar:
        for playlist in bar:
            tracks = get_tracks_of_playlist(playlist['id'])
            tag_tracks = read_tags_from_spotify_tracks(tracks)
            all_tracks_tags.extend(tag_tracks)

    return all_tracks_tags


def get_liked_tracks_count():
    results = sp.current_user_saved_tracks(limit=50)
    total_likes_count = results['total']
    return total_likes_count


def get_liked_tracks():
    tracks = []

    log.info(f'Collecting liked tracks')

    with click.progressbar(length=100, label='Collecting liked tracks') as bar:
        results = sp.current_user_saved_tracks(limit=50)
        total_likes_count = results['total']
        tracks.extend(results['items'])

        bar.length = total_likes_count
        bar.update(len(tracks))

        log.debug(f'Collected {len(tracks)}/{total_likes_count}')

        while results['next']:
            results = sp.next(results)
            tracks.extend(results['items'])
            bar.update(len(tracks))

            log.debug(f'Collected {len(tracks)}/{total_likes_count}')

    return tracks


def add_tracks_to_liked(track_ids):
    for i in range(len(track_ids)):
        track_ids[i] = parse_track_id(track_ids[i])

    log.info(f'Adding {len(track_ids)} to saved tracks')

    i = 0
    next_tracks = []
    while i < len(track_ids):
        next_tracks.append(track_ids[i])
        if len(next_tracks) == 50 or i == len(track_ids) - 1:
            sp.current_user_saved_tracks_add(tracks=next_tracks)
            log.debug(f'Added {i + 1}/{len(next_tracks)} tracks to saved')
            next_tracks = []
        i += 1


def export_liked_tracks_to_file(file_name):
    log.info(f'Exporting liked tracks from file "{file_name}"')

    liked_tracks = get_liked_tracks()
    tag_tracks = read_tags_from_spotify_tracks(liked_tracks)
    spoty.csv_playlist.write_tags_to_csv(tag_tracks, file_name)

    log.success(f'{len(liked_tracks)} liked tracks exported to file: "{file_name}"')

    return liked_tracks


def import_likes_from_file(file_name):
    log.info(f'Importing liked tracks from file "{file_name}"')
    tracks_in_file = spoty.csv_playlist.read_tags_from_csv(file_name)
    if len(tracks_in_file) > 0:
        add_tracks_to_liked(tracks_in_file)

    log.success(f'{len(tracks_in_file)} liked tracks imported from file: "{file_name}"')

    return tracks_in_file


def get_likes_for_tracks(track_ids):
    likes = []

    i = 0
    next_tracks = []
    while i < len(track_ids):
        next_tracks.append(track_ids[i])
        if len(next_tracks) == 50 or i == len(track_ids) - 1:
            likes_new = sp.current_user_saved_tracks_contains(tracks=next_tracks)
            likes.extend(likes_new)
            next_tracks = []
        i += 1

    return likes


def get_liked_track_ids(track_ids):
    liked_tracks = []

    likes = get_likes_for_tracks(track_ids)
    for i in range(len(track_ids)):
        if likes[i]:
            liked_tracks.append(track_ids[i])

    return liked_tracks


def get_not_liked_track_ids(track_ids):
    not_liked_tracks = []

    likes = get_likes_for_tracks(track_ids)
    for i in range(len(track_ids)):
        if not likes[i]:
            not_liked_tracks.append(track_ids[i])

    return not_liked_tracks


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


def check_is_user_URI(uri):
    return uri.startswith("https://open.spotify.com/user/")


def parse_playlist_id(id_or_uri):
    if (id_or_uri.startswith("https://open.spotify.com/playlist/")):
        id_or_uri = id_or_uri.split('/playlist/')[1]
        id_or_uri = id_or_uri.split('?')[0]
    return id_or_uri


def parse_track_id(id_or_uri):
    if (id_or_uri.startswith("https://open.spotify.com/track/")):
        id_or_uri = id_or_uri.split('/track/')[1]
        id_or_uri = id_or_uri.split('?')[0]
    return id_or_uri


def parse_user_id(id_or_uri):
    if (id_or_uri.startswith("https://open.spotify.com/user/")):
        id_or_uri = id_or_uri.split('/user/')[1]
        id_or_uri = id_or_uri.split('?')[0]
    return id_or_uri


def get_playlist_file_name(playlist_name, playlist_id, path, avoid_filenames):
    playlist_name = spoty.utils.slugify_file_pah(playlist_name)
    if (len(playlist_name) == 0):
        playlist_name = playlist_id
    full_file_name = os.path.join(path, playlist_name + ".csv")

    if full_file_name in avoid_filenames:
        full_file_name = get_playlist_file_name(playlist_name + " (1)", playlist_id, path, avoid_filenames)

    return full_file_name


def read_tags_from_spotify_tracks(tracks):
    tag_tracks = []

    for track in tracks:
        tags = read_tags_from_spotify_track(track)
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

    for tag in spoty.utils.spoty_tags:
        if tag in track:
            tags[tag] = track[tag]

    return tags


def filter_spotify_tracks_which_have_all_tags(spotify_track, filter_tags):
    filtered = []
    for track in spotify_track:
        tags = read_tags_from_spotify_track(track)
        if spoty.utils.check_all_tags_exist(tags, filter_tags):
            filtered.append(track)
    return filtered


def filter_spotify_tracks_which_not_have_any_of_tags(spotify_track, filter_tags):
    filtered = []
    for track in spotify_track:
        tags = read_tags_from_spotify_track(track)
        if not spoty.utils.check_all_tags_exist(tags, filter_tags):
            filtered.append(track)
    return filtered
