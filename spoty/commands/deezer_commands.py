from spoty import settings
from spoty import log
from spoty.utils import *
import spoty.deezer
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
    spoty.deezer.get_token()
    pass


@auth.command("get-token-manualy")
def auth_get_token():
    r"""Get deezer access token manually.

    When starting the command, further actions will be described.
    """
    deezy.auth_manualy.get_token()
    pass


@deezer.group()
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

        deezy playlist list

        deezy playlist list --user-id 4717400682
    """
    if user_id == None:
        playlists = spoty.deezer.get_list_of_playlists()
    else:
        playlists = spoty.deezer.get_list_of_user_playlists(user_id)

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

        deezy playlist create "My awesome playlist"
    """
    id = spoty.deezer.create_playlist(name)
    click.echo(f'New playlist created (id: {id}, name: "{name}")')


@playlist.command("delete")
@click.argument("playlist_id", type=str, nargs=-1)
@click.option('--confirm', '-y', type=bool, is_flag=True, default=False,
              help='Do not ask for export confirmation')
def playlist_delete(playlist_id, confirm):
    r"""
    Delete playlists with the specified id.

    PLAYLIST_IDS - list of playlist IDs or URIs. You can specify one ID or many IDs separated by a space.

    Examples:

        deezy playlist delete 9457847341

        deezy playlist delete 9457847341 --confirm

        deezy playlist delete 9457847341 9712468342

        deezy playlist delete https://www.deezer.com/ru/playlist/9457847341
    """
    deleted_playlists = spoty.deezer.delete_playlist(playlist_id, confirm)
    click.echo(f'{len(deleted_playlists)} playlist deleted')


@playlist.command("delete-all")
@click.option('--confirm', '-y', type=bool, is_flag=True, default=False,
              help='Do not ask for export confirmation')
def playlist_delete_all(confirm):
    r"""
    Delete playlists with the specified id.

    Examples:

        deezy playlist delete-all

        deezy playlist delete-all --confirm
    """
    deleted_playlists = spoty.deezer.delete_all_playlist(confirm)
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
#         deezy playlist copy 9457847341
#
#         deezy playlist copy 9457847341 9712468342
#
#         deezy playlist copy https://www.deezer.com/ru/playlist/9457847341
#
#     """
#
# playlists = []
# tracks = []
# with click.progressbar(playlist_ids, label='Copying playlists') as bar:
#     for playlist_id in bar:
#         new_playlist_id, tracks_added = spoty.deezer.copy_playlist(playlist_id)
#         playlists.extend(new_playlist_id)
#         tracks.extend(tracks_added)
#
# click.echo(f'{len(playlists)} playlists with {len(tracks)} tracks copied.')


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

        deezy playlist add-tracks 9457847341 74359352

        deezy playlist add-tracks 9457847341 74359352 14456300

        deezy playlist add-tracks https://www.deezer.com/ru/playlist/9457847341 https://www.deezer.com/ru/track/74359352

    """
    tracks_added = spoty.deezer.add_tracks_to_playlist(playlist_id, track_ids, allow_duplicates)
    click.echo(f'{len(tracks_added)} tracks added to playlist {playlist_id}')


@playlist.command("read")
@click.argument("playlist_ids", type=str, nargs=-1)
def playlist_read(playlist_ids):
    r"""
    Read playlists and print track ids.
    it could be your playlists or created by another user.

    PLAYLIST_IDS - list of playlist IDs or URIs. You can specify one ID or many IDs separated by a space.

    Examples:

        deezy playlist read 9457847341

        deezy playlist read 9457847341 9712468342

        deezy playlist read https://www.deezer.com/ru/playlist/9457847341

    """

    playlists_dict = spoty.deezer.get_playlists_with_full_list_of_tracks(playlist_ids)

    for playlist_id, tracks_list in playlists_dict.items():
        click.echo(f'Tracks in playlist {playlist_id}:')
        for track in tracks_list:
            title = spoty.deezer.get_track_artist_and_title(track)
            click.echo(f'{track["SNG_ID"]} "{title}"')

        click.echo(f'Total tracks: {len(tracks_list)}')

