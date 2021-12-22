import deezer.errors
from spoty import settings
from deezer import Deezer
from spoty import log
import spoty.utils
import os.path
import click
import time
import re

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
    user_id = parse_user_id(user_id)
    if user_id == 'me':
        playlists = get_list_of_playlists()
        click.echo(f'You have {len(playlists)} playlists in Deezer library')
    else:
        playlists = get_list_of_user_playlists(user_id)
        click.echo(f'User {user_id} has {len(playlists)} playlists in Deezer library')

    if playlists_names_regex is not None:
        playlists = list(filter(lambda pl: re.findall(playlists_names_regex, pl['name']), playlists))

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


def find_tracks_by_isrc(isrcs_list):
    isrcs_list = list(filter(lambda isrc: len(isrc) > 0, isrcs_list))
    isrcs_list = spoty.utils.remove_duplicates(isrcs_list)

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
    track_ids = spoty.utils.remove_duplicates(track_ids)

    for i in range(len(track_ids)):
        track_ids[i] = parse_track_id(track_ids[i])

    log.info(f'Adding {len(track_ids)} tracks to playlist {playlist_id}')

    playlist = get_playlist(playlist_id)

    if not allow_duplicates:
        tracks, playlist = get_playlist_with_full_list_of_tracks(playlist_id)
        existing_ids = get_track_ids(tracks)
        new_ids = spoty.utils.filter_duplicates(existing_ids, track_ids)
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
        tags['LENGTH'] = int(track['DURATION']) * 1000

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

    # try:
    #     tags['YEAR'] = track['album']['release_date']
    # except:
    #     pass

    for tag in spoty.utils.spoty_tags:
        if tag in track:
            tags[tag] = track[tag]

    return tags
