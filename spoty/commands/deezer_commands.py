from spoty import settings
from spoty import log
import spoty.deezer_auth
import spoty.deezer_auth_manualy
import spoty.utils
import spoty.deezer_api
import click
import re
import time
import os
from datetime import datetime


@click.group()
def deezer():
    r"""Deezer specific commands."""
    pass


@deezer.group()
def auth():
    r"""Deezer authorization."""
    pass


@auth.command("get-token")
def auth_get_token():
    r"""
    Get deezer access token automatically using a local server.

    When the token is received, it will be written to the configuration file.
    """
    spoty.deezer_auth.get_token()
    pass


@auth.command("get-token-manualy")
def auth_get_token():
    r"""Get deezer access token manually.

    When starting the command, further actions will be described.
    """
    spoty.deezer_auth_manualy.get_token()
    pass


@deezer.group()
def playlist():
    r"""Playlists management."""
    pass


@playlist.command("list")
@click.option('--filter-names',
              help='List only playlists whose names matches this regex filter')
@click.option('--user-id',  help='Get playlists of this user')
def playlist_list(filter_names, user_id):
    r"""
    List of all playlists.

    Examples:

        spoty deezer playlist list

        spoty deezer playlist list --user-id 4717400682
    """
    if user_id == None:
        playlists = spoty.deezer_api.get_list_of_user_playlists()
    else:
        playlists = spoty.deezer_api.get_list_of_user_playlists(user_id)

    if len(playlists) == 0:
        exit()

    if filter_names is not None:
        playlists = list(filter(lambda pl: re.findall(filter_names, pl['title']), playlists))
        click.echo(f'{len(playlists)} playlists matches the filter')

    if len(playlists) == 0:
        exit()

    for playlist in playlists:
        click.echo(f'{playlist["id"]} "{playlist["title"]}"')

    click.echo(f'Total playlists: {len(playlists)}')


@playlist.command("create")
@click.argument("name", type=str)
def playlist_create(name):
    r"""
    Create a new empty playlist with the specified name.

    Examples:

        spoty deezer playlist create "My awesome playlist"
    """
    id = spoty.deezer_api.create_playlist(name)
    click.echo(f'New playlist created (id: {id}, name: "{name}")')


@playlist.command("delete")
@click.argument("playlist_id",  nargs=-1)
@click.option('--confirm', '-y',  is_flag=True, 
              help='Do not ask for export confirmation')
def playlist_delete(playlist_id, confirm):
    r"""
    Delete playlists with the specified id.

    PLAYLIST_IDS - list of playlist IDs or URIs. You can specify one ID or many IDs separated by a space.

    Examples:

        spoty deezer playlist delete 9457847341

        spoty deezer playlist delete 9457847341 --confirm

        spoty deezer playlist delete 9457847341 9712468342

        spoty deezer playlist delete https://www.deezer.com/ru/playlist/9457847341
    """
    deleted_playlists = spoty.deezer_api.delete_playlists(playlist_id, confirm)
    click.echo(f'{len(deleted_playlists)} playlist deleted')


@playlist.command("delete-all")
@click.option('--confirm', '-y',  is_flag=True, 
              help='Do not ask for export confirmation')
def playlist_delete_all(confirm):
    r"""
    Delete all playlists in the library.

    Examples:

        spoty deezer playlist delete-all

        spoty deezer playlist delete-all --confirm
    """
    deleted_playlists = spoty.deezer_api.delete_all_playlists(confirm)
    click.echo(f'{len(deleted_playlists)} playlist deleted')


# @playlist.command("copy")
# @click.argument("playlist_ids", type=str, nargs=-1)
# def playlist_copy(playlist_ids):
#     r"""
#     Create copies of playlists.
#     it could be your playlists or created by another user.
#     The exact same playlists will be created in your library.
#
#     PLAYLIST_IDS - list of playlist IDs or URIs. You can specify one ID or many IDs separated by a space.
#
#
#
#     Examples:
#
#         spoty deezer playlist copy 9457847341
#
#         spoty deezer playlist copy 9457847341 9712468342
#
#         spoty deezer playlist copy https://www.deezer.com/ru/playlist/9457847341
#
#     """
#
# playlists = []
# tracks = []
# with click.progressbar(playlist_ids, label='Copying playlists') as bar:
#     for playlist_id in bar:
#         new_playlist_id, tracks_added = spoty.deezer_api.copy_playlist(playlist_id)
#         playlists.extend(new_playlist_id)
#         tracks.extend(tracks_added)
#
# click.echo(f'{len(playlists)} playlists with {len(tracks)} tracks copied.')


@playlist.command("add-tracks")
@click.argument("playlist_id", )
@click.argument("track_ids",  nargs=-1)
@click.option('--allow-duplicates', '-d',  is_flag=True, 
              help='Add tracks that are already in the playlist.')
def playlist_add_tracks(playlist_id, track_ids, allow_duplicates):
    r"""
    Add tracks to playlist.

    PLAYLIST_ID - playlist ID or URI.

    TRACK_IDS - list of track IDs or URIs. You can specify one ID or many IDs separated by a space.

    Examples:

        spoty deezer playlist add-tracks 9457847341 74359352

        spoty deezer playlist add-tracks 9457847341 74359352 14456300

        spoty deezer playlist add-tracks https://www.deezer.com/ru/playlist/9457847341 https://www.deezer.com/ru/track/74359352

    """
    tracks_added, import_duplicates, already_exist \
        = spoty.deezer_api.add_tracks_to_playlist_by_ids(playlist_id, track_ids, allow_duplicates)
    click.echo(f'{len(tracks_added)} tracks added to playlist {playlist_id}')


@playlist.command("read")
@click.argument("playlist_ids",  nargs=-1)
def playlist_read(playlist_ids):
    r"""
    Read playlists and print track ids.
    it could be your playlists or created by another user.

    PLAYLIST_IDS - list of playlist IDs or URIs. You can specify one ID or many IDs separated by a space.

    Examples:

        spoty deezer playlist read 9457847341

        spoty deezer playlist read 9457847341 9712468342

        spoty deezer playlist read https://www.deezer.com/ru/playlist/9457847341

    """

    playlist_ids = spoty.utils.tuple_to_list(playlist_ids)
    playlists_dict = spoty.deezer_api.get_playlists_with_full_list_of_tracks(playlist_ids)

    for playlist_id, tracks_list in playlists_dict.items():
        click.echo(f'Tracks in playlist {playlist_id}:')
        for track in tracks_list:
            title = spoty.deezer_api.get_track_artist_and_title(track)
            click.echo(f'{track["SNG_ID"]} "{title}"')

        click.echo(f'Total tracks: {len(tracks_list)}')


@deezer.group()
def track():
    r"""Track management."""
    pass

@track.command("id")
@click.argument("id")
def track_find_by_id(id):
    r"""
    Find track by ID.
    """
    track = spoty.deezer_api.find_track_by_id(id)
    if track == None:
        click.echo("Not found")
        return
    tags = spoty.deezer_api.read_tags_from_deezer_track(track)
    spoty.utils.print_main_tags(tags)
