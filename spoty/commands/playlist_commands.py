from spoty import settings
from spoty import log
import spoty.playlist
import spoty.like
import click
import re
import spoty.utils
import time
import os
from datetime import datetime


@click.group()
def playlist():
    r"""Playlists management."""
    pass


@playlist.command("list")
@click.option('--filter-names', type=str, default=None,
              help='List only playlists whose names matches this regex filter')
@click.option('--user-id', type=str, default=None, help='Get playlists of this user')
def playlist_list(filter_names, user_id):
    r"""
    List of all playlists.

    Examples:

        spoty playlist list

        spoty playlist list --user-id 4717400682
    """
    if user_id == None:
        playlists = spoty.playlist.get_list_of_playlists()
    else:
        playlists = spoty.playlist.get_list_of_user_playlists(user_id)

    if len(playlists) == 0:
        exit()

    if filter_names is not None:
        playlists = list(filter(lambda pl: re.findall(filter_names, pl['name']), playlists))
        click.echo(f'{len(playlists)} playlists matches the filter')

    if len(playlists) == 0:
        exit()

    for playlist in playlists:
        click.echo(f'{playlist["id"]} "{playlist["name"]}"')

    click.echo(f'Total playlists: {len(playlists)}')


@playlist.command("list")
@click.option('--filter-names', type=str, default=None,
              help='List only playlists whose names matches this regex filter')
@click.option('--user-id', type=str, default=None, help='Get playlists of this user')
def playlist_list(filter_names, user_id):
    r"""
    List of all playlists.

    Examples:

        spoty playlist list

        spoty playlist list --user-id 4717400682
    """
    if user_id == None:
        playlists = spoty.playlist.get_list_of_playlists()
    else:
        playlists = spoty.playlist.get_list_of_user_playlists(user_id)

    if len(playlists) == 0:
        exit()

    if filter_names is not None:
        playlists = list(filter(lambda pl: re.findall(filter_names, pl['name']), playlists))
        click.echo(f'{len(playlists)} playlists matches the filter')

    if len(playlists) == 0:
        exit()

    for playlist in playlists:
        click.echo(f'{playlist["id"]} "{playlist["name"]}"')

    click.echo(f'Total playlists: {len(playlists)}')


@playlist.command("create")
@click.argument("name", type=str)
def playlist_create(name):
    r"""
    Create a new empty playlist with the specified name.

    Examples:

        spoty playlist create "My awesome playlist"
    """
    id = spoty.playlist.create_playlist(name)
    click.echo(f'New playlist created (id: {id}, name: "{name}")')


@playlist.command("copy")
@click.argument("playlist_ids", type=str, nargs=-1)
def playlist_copy(playlist_ids):
    r"""
    Create copies of playlists.
    it could be your playlists or created by another user.
    The exact same playlists will be created in your library.

    PLAYLIST_IDS - list of playlist IDs or URIs. You can specify one ID or many IDs separated by a space.



    Examples:

        spoty playlist copy 37i9dQZF1DX8z1UW9HQvSq

        spoty playlist copy 37i9dQZF1DX8z1UW9HQvSq 37i9dQZF1DX7jNFrjYQurt

        spoty playlist copy https://open.spotify.com/playlist/37i9dQZF1DX8z1UW9HQvSq

    """
    playlists = []
    tracks = []
    with click.progressbar(playlist_ids, label='Copying playlists') as bar:
        for playlist_id in bar:
            new_playlist_id, tracks_added = spoty.playlist.copy_playlist(playlist_id)
            playlists.extend(new_playlist_id)
            tracks.extend(tracks_added)

    click.echo(f'{len(playlists)} playlists with {len(tracks)} tracks copied.')


@playlist.command("add-tracks")
@click.argument("playlist_id", type=str)
@click.argument("track_ids", type=str, nargs=-1)
@click.option('--allow-duplicates', '-d', type=bool, is_flag=True, default=False,
              help='Add tracks that are already in the playlist.')
def playlist_add_tracks(playlist_id, track_ids, allow_duplicates):
    r"""
    Add tracks to playlist.

    PLAYLIST_ID - playlist ID or URI.

    TRACK_IDS - list of track IDs or URIs. You can specify one ID or many IDs separated by a space.

    Examples:

        spoty playlist add-tracks 37i9dQZF1DX8z1UW9HQvSq 00i9VF7sjSaTqblAuKFBDO

        spoty playlist add-tracks 37i9dQZF1DX8z1UW9HQvSq 00i9VF7sjSaTqblAuKFBDO 7cjlfruK9Oqw7k5wAZGO72

        spoty playlist add-tracks https://open.spotify.com/playlist/37i9dQZF1DX8z1UW9HQvSq https://open.spotify.com/track/00i9VF7sjSaTqblAuKFBDO

    """
    track_ids = list(track_ids)
    tracks_added = spoty.playlist.add_tracks_to_playlist(playlist_id, track_ids, allow_duplicates)
    click.echo(f'{len(tracks_added)} tracks added to playlist {playlist_id}')


@playlist.command("remove-tracks")
@click.argument("playlist_id", type=str)
@click.argument("track_ids", type=str, nargs=-1)
def playlist_remove_tracks(playlist_id, track_ids):
    r"""
    Remove tracks from playlist.

    PLAYLIST_ID - playlist ID or URI.

    TRACK_IDS - list of track IDs or URIs. You can specify one ID or many IDs separated by a space.

    Examples:

        spoty playlist remove-tracks 37i9dQZF1DX8z1UW9HQvSq 00i9VF7sjSaTqblAuKFBDO

        spoty playlist remove-tracks 37i9dQZF1DX8z1UW9HQvSq 00i9VF7sjSaTqblAuKFBDO 7cjlfruK9Oqw7k5wAZGO72

        spoty playlist remove-tracks https://open.spotify.com/playlist/37i9dQZF1DX8z1UW9HQvSq https://open.spotify.com/track/00i9VF7sjSaTqblAuKFBDO

    """
    track_ids = list(track_ids)
    spoty.playlist.remove_tracks_from_paylist(playlist_id, track_ids)
    click.echo(f'Tracks removed from playlist {playlist_id}')


@playlist.command("remove-liked-tracks")
@click.argument("playlist_ids", type=str, nargs=-1)
def playlist_remove_liked_tracks(playlist_ids):
    r"""
    Read playlists and remove all liked tracks found from these playlists.

    PLAYLIST_IDS - list of playlist IDs or URIs. You can specify one ID or many IDs separated by a space.

    Examples:

        spoty playlist remove-liked-tracks 37i9dQZF1DX8z1UW9HQvSq

        spoty playlist remove-liked-tracks 37i9dQZF1DX8z1UW9HQvSq 37i9dQZF1DX7jNFrjYQurt

        spoty playlist remove-liked-tracks https://open.spotify.com/playlist/37i9dQZF1DX8z1UW9HQvSq

    """

    all_removed_tracks = []
    with click.progressbar(playlist_ids, label='Removing liked tracks from playlists') as bar:
        for playlist_id in bar:
            removed_tracks = spoty.playlist.remove_liked_tracks_in_playlist(playlist_id)
            all_removed_tracks.extend(removed_tracks)

    click.echo(f'{len(all_removed_tracks)} liked tracks removed from {len(playlist_ids)} playlists.')


@playlist.command("list-invalid-tracks")
@click.argument("playlist_ids", type=str, nargs=-1)
def playlist_list_invalid_tracks(playlist_ids):
    r"""
    Read playlists and list all invalid tracks found from these playlists.
    Tracks that have no ID are considered invalid.
    If a track is not available in the given region it is not considered invalid. You can still pull information on it. Tracks that are not available for the region will not be deleted.
    Invalid tracks are those for which there is no information at all in the database (have been deleted from the spotify database).

    PLAYLIST_IDS - list of playlist IDs or URIs. You can specify one ID or many IDs separated by a space.

    Examples:

        spoty playlist list-invalid-tracks 37i9dQZF1DX8z1UW9HQvSq

        spoty playlist list-invalid-tracks 37i9dQZF1DX8z1UW9HQvSq 37i9dQZF1DX7jNFrjYQurt

        spoty playlist list-invalid-tracks https://open.spotify.com/playlist/37i9dQZF1DX8z1UW9HQvSq

    """

    all_invalid_tracks = []
    with click.progressbar(playlist_ids, label='Collecting invalid tracks from playlists') as bar:
        for playlist_id in bar:
            removed_tracks = spoty.playlist.get_invalid_tracks_in_playlist(playlist_id)
            all_invalid_tracks.extend(removed_tracks)

    click.echo(f'{len(all_invalid_tracks)} invalid tracks in {len(playlist_ids)} playlists.')

    if len(all_invalid_tracks) > 0:
        for track in all_invalid_tracks:
            click.echo(str(track))


@playlist.command("like-all-tracks")
@click.argument("playlist_ids", type=str, nargs=-1)
def playlist_like_all_tracks(playlist_ids):
    r"""
    Read playlists and like all tracks in these playlists.

    PLAYLIST_IDS - list of playlist IDs or URIs. You can specify one ID or many IDs separated by a space.

    Examples:

        spoty playlist like-all-tracks 37i9dQZF1DX8z1UW9HQvSq

        spoty playlist like-all-tracks 37i9dQZF1DX8z1UW9HQvSq 37i9dQZF1DX7jNFrjYQurt

        spoty playlist like-all-tracks https://open.spotify.com/playlist/37i9dQZF1DX8z1UW9HQvSq

    """

    all_liked_tracks = []
    with click.progressbar(playlist_ids, label='Liking all tracks in playlists') as bar:
        for playlist_id in bar:
            liked_tracks = spoty.playlist.like_all_tracks_in_playlist(playlist_id)
            all_liked_tracks.extend(liked_tracks)

    click.echo(f'{len(all_liked_tracks)} tracks added to liked tracks in {len(playlist_ids)} playlists.')


@playlist.command("read")
@click.argument("playlist_ids", type=str, nargs=-1)
def playlist_read(playlist_ids):
    r"""
    Read playlists and print track ids.
    it could be your playlists or created by another user.

    PLAYLIST_IDS - list of playlist IDs or URIs. You can specify one ID or many IDs separated by a space.

    Examples:

        spoty playlist read 37i9dQZF1DX8z1UW9HQvSq

        spoty playlist read 37i9dQZF1DX8z1UW9HQvSq 37i9dQZF1DX7jNFrjYQurt

        spoty playlist read https://open.spotify.com/playlist/37i9dQZF1DX8z1UW9HQvSq

    """
    for playlist_id in playlist_ids:
        click.echo(f'Tracks in playlist {playlist_id}:')
        tracks = spoty.playlist.get_tracks_of_playlist(playlist_id)
        for track in tracks:
            title = spoty.utils.get_track_artist_and_title(track["track"])
            click.echo(f'{track["track"]["id"]}: {title}')

    click.echo(f'Total tracks: {len(tracks)}')


@playlist.command("export")
@click.option('--path', type=str, default=settings.DEFAULT_LIBRARY_PATH, help='Path to create files')
@click.option('--overwrite', '-o', type=bool, is_flag=True, default=False,
              help='Overwrite existing files without asking')
@click.argument("playlist_ids", type=str, nargs=-1)
def playlist_export(path, playlist_ids, overwrite):
    r"""Export playlists to csv files on disk.
    it could be your playlists or created by another user.

    PLAYLIST_IDS - list of playlist IDs or URIs. You can specify one ID or many IDs separated by a space.

    Examples:

        spoty playlist export 37i9dQZF1DX8z1UW9HQvSq

        spoty playlist export --path "C:\Users\User\Downloads" 37i9dQZF1DX8z1UW9HQvSq 37i9dQZF1DX7jNFrjYQurt

        spoty playlist export https://open.spotify.com/playlist/37i9dQZF1DX8z1UW9HQvSq
    """

    path = os.path.abspath(path)

    file_names = []
    with click.progressbar(playlist_ids, label='Exporting playlists') as bar:
        for playlist_id in bar:
            file_name = spoty.playlist.export_playlist_to_file(playlist_id, path, overwrite)
            if file_name is not None:
                file_names.append(file_name)

    log.success(f'{len(file_names)} playlists exported to path: "{path}"')
    click.echo(f'{len(file_names)} playlists exported to path: "{path}"')


@playlist.command("export-all")
@click.option('--path', type=str, default=settings.DEFAULT_LIBRARY_PATH, help='Path to create files')
@click.option('--filter-names', type=str, default=None,
              help='Export only playlists whose names matches this regex filter')
@click.option('--user-id', type=str, default=None, help='Get playlists of this user')
@click.option('--overwrite', '-o', type=bool, is_flag=True, default=False,
              help='Overwrite existing files without asking')
@click.option('--confirm', '-c', type=bool, is_flag=True, default=False,
              help='Do not ask for export confirmation')
@click.option('--timestamp', '-t', type=bool, is_flag=True, default=False,
              help='Create a subfolder with the current date and time (it can be convenient for creating backups')
def playlist_export_all(path, filter_names, user_id, overwrite, confirm, timestamp):
    r"""Export all playlists from your library to csv files on disk.

    Examples:

        spoty playlist export-all

        spoty playlist export-all --path "C:\Users\User\Downloads"

        Export only playlists whose names starts with "awesome":

            spoty playlist export-all --filter-names "^awesome"
    """

    path = os.path.abspath(path)

    if user_id == None:
        playlists = spoty.playlist.get_list_of_playlists()
        click.echo(f'You have {len(playlists)} playlists')
    else:
        playlists = spoty.playlist.get_list_of_user_playlists(user_id)
        click.echo(f'User has {len(playlists)} playlists')

    if len(playlists) == 0:
        exit()

    if filter_names is not None:
        playlists = list(filter(lambda pl: re.findall(filter_names, pl['name']), playlists))
        click.echo(f'{len(playlists)} playlists matches the filter')

    if len(playlists) == 0:
        exit()

    click.echo(f'The following playlists will be exported:')
    for playlist in playlists:
        click.echo(playlist['name'])

    click.echo(f'Total playlists: {len(playlists)}')

    if not confirm:
        click.confirm('Do you want to continue?', abort=True)

    if timestamp:
        now = datetime.now()
        date_time_str = now.strftime("%Y_%m_%d-%H_%M_%S")
        path = os.path.join(path, date_time_str)

    file_names = []
    with click.progressbar(playlists, label='Exporting playlists') as bar:
        for playlist in bar:
            file_name = spoty.playlist.export_playlist_to_file(playlist['id'], path, overwrite, file_names)
            if file_name is not None:
                file_names.append(file_name)

    log.success(f'{len(file_names)} playlists exported to path: "{path}"')
    click.echo(f'{len(file_names)} playlists exported to path: "{path}"')


@playlist.command("import")
@click.argument('file_names', type=str, nargs=-1)
@click.option('--append', '-a', type=bool, is_flag=True, default=False,
              help='Add tracks to an existing playlist, if there is one with the same name. If the parameter is not specified, a new playlist will always be created.')
@click.option('--allow-duplicates', '-d', type=bool, is_flag=True, default=False,
              help='Add tracks that are already in the playlist.')
def playlist_import(file_names, append, allow_duplicates):
    r"""Import playlists to yor library from csv files on disk.

    FILE_NAMES - list of file names to import. You can specify one file or many files separated by a space.

    Examples:

        spoty playlist import "C:\Users\User\Downloads\export\playlist1.csv"

        spoty playlist import "C:\Users\User\Downloads\export\playlist1.csv" "C:\Users\User\Downloads\export\playlist2.csv"

        spoty playlist import --append "C:\Users\User\Downloads\export\playlist1.csv"

    """
    with click.progressbar(file_names, label='Importing playlists') as bar:
        all_tracks_added = []
        all_tracks_in_file = []
        for file_name in bar:
            try:
                playlist_id, tracks_added, tracks_in_file = spoty.playlist.import_playlist_from_file(file_name, append,
                                                                                                     allow_duplicates)
                all_tracks_added += tracks_added
                all_tracks_in_file += tracks_in_file
            except FileNotFoundError:
                time.sleep(0.2)  # waiting progressbar updating
                click.echo(f'\nFile does not exist: "{file_name}"')
            except spoty.playlist.CSVFileEmpty as e:
                log.warning(f'Cant import file "{file_name}". File is empty.')
                time.sleep(0.2)  # waiting progressbar updating
                click.echo(f'\nCant import file "{file_name}". File is empty.')
            except spoty.playlist.CSVFileInvalidHeader as e:
                log.error(
                    f'Cant import file "{file_name}". The header of csv table does not contain any of the required ' \
                    f'fields (isrc, spotify_track_id, title).')
                time.sleep(0.2)  # waiting progressbar updating
                click.echo(
                    f'\nCant import file "{file_name}". The header of csv table does not contain any of the required ' \
                    f'fields (isrc, spotify_track_id, title).')

            time.sleep(0.2)
    click.echo(
        f'Imported {len(all_tracks_added)} new tracks from {len(file_names)} playlists (total tracks in files: {len(all_tracks_in_file)})')


@playlist.command("import-all")
@click.argument('path', type=str, default=settings.DEFAULT_LIBRARY_PATH)
@click.option('--append', '-a', type=bool, is_flag=True, default=False,
              help='Add tracks to an existing playlist, if there is one with the same name. If the parameter is not specified, a new playlist will always be created.')
@click.option('--allow-duplicates', '-d', type=bool, is_flag=True, default=False,
              help='Add tracks that are already in the playlist.')
@click.option('--filter-names', type=str, default=None,
              help='Export only playlists whose names matches this regex filter')
@click.option('--confirm', '-c', type=bool, is_flag=True, default=False,
              help='Do not ask for export confirmation')
@click.pass_context
def playlist_import_all(ctx, path, append, allow_duplicates, filter_names, confirm):
    r"""Import all playlists to your library from csv files on disk.

    PATH - Path to files for import

    Examples:

        spoty playlist import-all "C:\Users\User\Downloads\export"

        Import only playlists whose names starts with "awesome":

            spoty playlist import-all --filter-names "^awesome" "C:\Users\User\Downloads\export"
    """

    path = os.path.abspath(path)

    file_names = []
    full_file_names = []
    for (dirpath, dirnames, filenames) in os.walk(path):
        file_names.extend(filenames)
        break

    if len(file_names) == 0:
        click.echo(f'No files found in path: {path}')
        exit()

    if filter_names is not None:
        file_names = list(filter(lambda file: re.findall(filter_names, file), file_names))

    if len(file_names) == 0:
        click.echo(f'No files that match the filter found in path: {path}')
        exit()

    for name in file_names:
        full_file_names.append(os.path.join(path, name))

    click.echo(f'The following files will be imported from path "{path}":')
    for name in file_names:
        click.echo(name)

    click.echo(f'Total files: {len(file_names)}')

    if not confirm:
        click.confirm('Do you want to continue?', abort=True)

    ctx.invoke(playlist_import, file_names=full_file_names, append=append, allow_duplicates=allow_duplicates)
