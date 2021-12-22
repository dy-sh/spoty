import deezer.errors
from spoty import settings
from deezer import Deezer
from spoty import log
import spoty.utils
import os.path
import click
import time
import re
import datetime

DEEZER_APP_ID = settings.default.DEEZER_APP_ID
DEEZER_APP_SECRET = settings.default.DEEZER_APP_SECRET
DEEZER_ACCESS_TOKEN = settings.default.DEEZER_ACCESS_TOKEN
DEEZER_REDIRECT_URI = settings.DEEZER.REDIRECT_URI
arl_file_name = os.path.join(spoty.config_path, '.arl')

dz = None


def get_dz():
    global dz
    if dz is None:
        dz = Deezer()
        get_arl()
    return dz


def request_valid_arl():
    while True:
        arl = input("Paste here your arl:")
        if get_dz().login_via_arl(arl.strip()): break
    return arl


def get_arl():
    if os.path.isfile(arl_file_name):
        with open(arl_file_name, 'r') as f:
            arl = f.readline().rstrip("\n").strip()
        if not get_dz().login_via_arl(arl): arl = request_valid_arl()
    else:
        arl = request_valid_arl()
    with open(arl_file_name, 'w') as f:
        f.write(arl)


def get_tracks_from_playlists(playlist_ids, add_extra_tags=True):
    all_tracks = []
    all_tags_list = []
    all_received_playlists = []

    requested_playlists = []

    with click.progressbar(playlist_ids, label=f'Reading tracks in {len(playlist_ids)} Deezer playlists') as bar:
        for playlist_id in bar:

            # remove already requested playlists
            if playlist_id in requested_playlists:
                click.echo(f'Deezer playlist {playlist_id} requested twice. In will be skipped.')
                continue

            tracks, playlist = get_playlist_with_full_list_of_tracks(playlist_id, add_extra_tags)
            requested_playlists.append(playlist_id)

            tags = read_tags_from_deezer_tracks(tracks)

            all_tracks.extend(tracks)
            all_tags_list.extend(tags)
            all_received_playlists.append(playlist_id)

    return all_tracks, all_tags_list, all_received_playlists


def get_tracks_of_deezer_user(user_id, playlists_names_regex=None):
    if user_id == 'me':
        playlists = get_list_of_user_playlists()
        click.echo(f'You have {len(playlists)} playlists in Deezer library')
    else:
        playlists = get_list_of_user_playlists(user_id)
        click.echo(f'User {user_id} has {len(playlists)} playlists in Deezer library')

    if playlists_names_regex is not None:
        playlists = list(filter(lambda pl: re.findall(playlists_names_regex, pl['title']), playlists))

    if len(playlists) == 0:
        return [], [], []

    ids = get_playlists_ids(playlists)
    tracks, tags, playlists = get_tracks_from_playlists(ids)

    return tracks, tags, playlists


def create_folder(folder_name):
    current_directory = os.getcwd()
    final_directory = os.path.join(current_directory, folder_name)
    if not os.path.exists(final_directory):
        os.makedirs(final_directory)


def get_track_artist_and_title(track):
    if track is None:
        return None

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


def get_track_ids(tracks):
    if len(tracks) == 0:
        return []
    else:
        return [str(track['SNG_ID']) for track in tracks]


def get_playlists_ids(playlists):
    if len(playlists) == 0:
        return []
    else:
        return [item['id'] for item in playlists]


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


def parse_user_id(id_or_url: str):
    id_or_url = str(id_or_url)
    if id_or_url.startswith("https://www.deezer.com/") and "/profile/" in id_or_url:
        id_or_url = id_or_url.split('/profile/')[1]
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


def get_playlist_with_full_list_of_tracks(playlist_id, add_extra_tags=True):
    playlist_id = parse_playlist_id(playlist_id)

    log.info(f'Collecting playlist {playlist_id}')

    playlist = get_dz().gw.get_playlist_page(playlist_id)
    tracks = get_dz().gw.get_playlist_tracks(playlist_id)

    playlist = playlist['DATA']

    log.debug(f'Playlist have {len(tracks)} tracks (playlist name: "{playlist["TITLE"]}")')

    if add_extra_tags:
        add_extra_tags_to_tracks([], tracks, playlist_id, playlist['TITLE'])

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


def get_list_of_user_playlists(user_id=None):
    if user_id is None:
        user_id = parse_user_id(get_dz().current_user['id'])
        # user_data = get_dz().gw.get_user_data()
        # user_id = user_data['USER']['USER_ID']
    playlists = get_dz().gw.get_user_playlists(user_id)
    return playlists


def delete_all_playlists(confirm=False):
    log.info(f'Deleting all playlist')

    playlists = get_list_of_user_playlists()

    if len(playlists) <= 1:
        log.debug("User has no playlists.")
        return []

    if not confirm:
        if not click.confirm(f'Are you sure you want to delete all {len(playlists)} playlists?'):
            log.info("Playlists not deleted. Canceled by user.")
            return []

    ids = [pl['id'] for pl in playlists]
    deleted_playlists = delete_playlists(ids, True)

    return deleted_playlists


def delete_playlists(playlist_ids, confirm=False):
    deleted_playlists = []
    with click.progressbar(playlist_ids, label=f'Deleting {len(playlist_ids)} playlists') as bar:
        for playlist_id in bar:
            res =delete_playlist(playlist_id, confirm)
            if res:
                deleted_playlists.append(playlist_id)

    return deleted_playlists


def delete_playlist(playlist_id, confirm=False):
    playlist_id = parse_playlist_id(playlist_id)

    log.info(f'Deleting playlist {playlist_id}')

    playlist = get_playlist(playlist_id)
    if playlist == None:
        log.info(f'Playlist {playlist_id} does not exist.')
        return False

    if not confirm:
        if not click.confirm(f'\nAre you sure you want to delete playlist "{playlist["TITLE"]}"?'):
            log.info("Playlist not deleted. Canceled by user.")
            return False
        click.echo()

    res = get_dz().gw.delete_playlist(playlist_id)
    if res:
        log.success(f'Playlist {playlist_id} deleted"')
        return True
    else:
        log.error(f'Playlist {playlist_id} not deleted"')
        return False


def add_track_release_dates(tracks):
    with click.progressbar(tracks, label=f'Reading albums') as bar:
        for track in bar:
            if 'DEEZER_ALBUM_ID' in track:
                track['YEAR'] = get_album_release_date(track['DEEZER_ALBUM_ID'])
            elif 'ALB_ID' in track:
                track['YEAR'] = get_album_release_date(track['ALB_ID'])
    return tracks


def get_album_release_date(album_id):
    album = get_dz().gw.get_album(album_id)
    if 'ORIGINAL_RELEASE_DATE' in album:
        return album['ORIGINAL_RELEASE_DATE']
    if 'PHYSICAL_RELEASE_DATE' in album:
        return album['PHYSICAL_RELEASE_DATE']
    if 'DIGITAL_RELEASE_DATE' in album:
        return album['DIGITAL_RELEASE_DATE']
    return None


def find_tracks_from_tags(tags_list):
    found_ids = []
    not_found_tracks = []

    for tags in tags_list:
        if "DEEZER_TRACK_ID" in tags:
            found_ids.append(tags['DEEZER_TRACK_ID'])
            continue

        if "ISRC" in tags:
            id = find_track_id_by_isrc(tags['ISRC'])
            if id is not None:
                found_ids.append(id)
                continue

        if "TITLE" in tags and "ARTIST" in tags:
            id = find_track_id_by_artist_and_title(tags['ARTIST'], tags['TITLE'], tags.get('ALBUM', None))
            if id is not None:
                found_ids.append(id)
                continue

        not_found_tracks.append(tags)

    return found_ids, not_found_tracks


def find_track_id_by_isrc(isrc):
    track = find_track_by_isrc(isrc)
    return track['id'] if track is not None else None


def find_track_by_isrc(isrc):
    try:
        track = get_dz().api.get_track_by_ISRC(isrc)
        log.debug(f'Track found by ISRC: {isrc} (ID: {track["id"]} TITLE: "{get_track_artist_and_title(track)}")')
        if track is not None and int(track['id']) != 0:
            return track
    except deezer.errors.DataException as e:
        log.debug(f'Track not found by ISRC: {isrc}"')

    return None


def find_track_id_by_artist_and_title(artist, title, album=""):
    track_id = get_dz().api.get_track_id_from_metadata(artist, title, album)
    return track_id if int(track_id) != 0 else None


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

    playlist = get_playlist(playlist_id)

    already_exist = []

    if not allow_duplicates:
        tracks, playlist = get_playlist_with_full_list_of_tracks(playlist_id)
        ids_in_playlist = get_track_ids(tracks)
        track_ids, already_exist = spoty.utils.remove_exist(ids_in_playlist, track_ids)
        if len(already_exist) > 0:
            log.debug(f'{len(already_exist)} tracks already exist and will be skipped.')

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

    return tracks_added, import_duplicates, already_exist


def find_playlist_by_name(name):
    playlists = get_list_of_user_playlists()
    return list(filter(lambda pl: pl['title'] == name, playlists))


def import_playlists_from_tags_list(tags_list, grouping_pattern, overwrite_if_exist=False, append_if_exist=False,
                                    allow_duplicates=True, confirm=False):
    all_playlist_ids = []
    all_tracks_added = []
    all_import_duplicates = []
    all_already_exist = []
    all_not_found = []
    grouped_tags = spoty.utils.group_tags_by_pattern(tags_list, grouping_pattern)

    with click.progressbar(length=len(grouped_tags), label=f'Importing {len(grouped_tags)} playlists') as bar:
        for group_name, g_tags_list in grouped_tags.items():
            playlist_id, tracks_added, import_duplicates, already_exist, not_found \
                = import_playlist_from_tags_list(group_name, g_tags_list, overwrite_if_exist, append_if_exist,
                                                 allow_duplicates, confirm)

            bar.update(1)

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


def remove_all_tracks_from_playlist(playlist_id, confirm=False):
    playlist_id = parse_playlist_id(playlist_id)

    playlist = get_playlist_with_full_list_of_tracks(playlist_id)
    tracks = playlist.tracks

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

    get_dz().gw.remove_songs_from_playlist(playlist_id, track_ids)

    # i = 0
    # next_tracks = []
    # while i < len(track_ids):
    #     track_ids[i] = parse_track_id(track_ids[i])
    #     next_tracks.append(track_ids[i])
    #     if len(next_tracks) == 100 or i == len(track_ids) - 1:
    #         get_dz().gw.remove_songs_from_playlist(playlist_id, next_tracks)
    #         next_tracks = []
    #     i += 1

    log.success(f'Tracks removed from playlist {playlist_id}')


def add_extra_tags_to_tracks(tracks, new_tracks, playlist_id, playlist_name):
    counter = len(tracks)
    for track in new_tracks:
        track['SPOTY_PLAYLIST_ID'] = playlist_id
        track['SPOTY_PLAYLIST_INDEX'] = counter + 1
        track['SPOTY_PLAYLIST_SOURCE'] = 'DEEZER'
        if playlist_name is not None:
            track['SPOTY_PLAYLIST_NAME'] = playlist_name
        try:
            track['SPOTY_TRACK_ID'] = track['SNG_ID']
        except:
            pass
        counter += 1
    return counter


def read_tags_from_deezer_tracks(tracks):
    tag_tracks = []

    for track in tracks:
        tags = read_tags_from_deezer_track(track)
        tag_tracks.append(tags)

    return tag_tracks


def read_tags_from_deezer_track(track):
    tags = {}

    if 'ISRC' in track:
        tags['ISRC'] = track['ISRC']

    if 'ART_NAME' in track:
        tags['ARTIST'] = track['ART_NAME']

    # try:
    #     artists = list(map(lambda artist: artist['ART_NAME'], track['ARTISTS']))
    #     tags['ARTIST'] = ';'.join(artists)
    # except:
    #     pass

    if 'SNG_TITLE' in track:
        tags['TITLE'] = track['SNG_TITLE']

    if 'ALB_TITLE' in track:
        tags['ALBUM'] = track['ALB_TITLE']

    if 'DURATION' in track:
        tags['SPOTY_LENGTH'] = int(track['DURATION']) * 1000

    if 'ALB_ID' in track:
        tags['DEEZER_ALBUM_ID'] = track['ALB_ID']

    if 'SNG_ID' in track:
        tags['WWWAUDIOFILE'] = f'https://www.deezer.com/track/{track["SNG_ID"]}'
        tags['DEEZER_TRACK_ID'] = track["SNG_ID"]

    if 'ART_ID' in track:
        tags['DEEZER_ARTIST_ID'] = track['ART_ID']

    try:
        tags['EXPLICIT'] = track['EXPLICIT_TRACK_CONTENT']['EXPLICIT_LYRICS_STATUS']
    except:
        pass

    if 'LYRICS_ID' in track:
        tags['DEEZER_LYRICS_ID'] = track['LYRICS_ID']

    if 'TRACK_NUMBER' in track:
        tags['TRACK'] = track['TRACK_NUMBER']

    if 'GAIN' in track:
        tags['GAIN'] = track['GAIN']

    if 'DATE_ADD' in track:
        timestamp = datetime.datetime.fromtimestamp(int(track['DATE_ADD']))
        # tags['DEZZER_DATE_ADD'] = track['DATE_ADD']
        tags['SPOTY_TRACK_ADDED'] = timestamp.strftime('%Y-%m-%d %H:%M:%S')

    # try:
    #     tags['YEAR'] = track['album']['release_date'] # get release date from album request
    # except:
    #     pass

    for tag in spoty.utils.spoty_tags:
        if tag in track:
            tags[tag] = track[tag]

    return tags
