from spoty import settings
from spoty import log
import spoty.spotify_api
import spoty.audio_files
import spoty.csv_playlist
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
@click.option('--filter-names', '--fn',
              help='List only playlists whose names matches this regex filter')
@click.option('--user-id', '--u',
              help='Get playlists of this user.')
@click.option('--followed', '-f', is_flag=True,
              help='List followed by user playlists instead of created by user (only for current user).')
def playlist_list(filter_names, user_id,followed):
    r"""
    List of all playlists.

    Examples:

        spoty spotify playlist list

        spoty spotify playlist list --user-id 4717400682
    """
    if user_id == None:
        playlists = spoty.spotify_api.get_list_of_playlists(not followed)
    else:
        playlists = spoty.spotify_api.get_list_of_user_playlists(user_id)

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


@playlist.command("read")
@click.argument("playlist_ids", nargs=-1)
def playlist_read(playlist_ids):
    r"""
    Read playlists and print track ids.
    it could be your playlists or created by another user.

    PLAYLIST_IDS - list of playlist IDs or URIs. You can specify one ID or many IDs separated by a space.

    Examples:

        spoty spotify playlist read 37i9dQZF1DX8z1UW9HQvSq

        spoty spotify playlist read 37i9dQZF1DX8z1UW9HQvSq 37i9dQZF1DX7jNFrjYQurt

        spoty spotify playlist read https://open.spotify.com/playlist/37i9dQZF1DX8z1UW9HQvSq

    """
    tracks = []
    for playlist_id in playlist_ids:
        click.echo(f'Tracks in playlist {playlist_id}:')
        tracks = spoty.spotify_api.get_tracks_of_playlist(playlist_id)
        for track in tracks:
            title = spoty.spotify_api.get_track_artist_and_title(track["track"])
            click.echo(f'{track["track"]["id"]}: {title}')

    click.echo(f'Total tracks: {len(tracks)}')


@playlist.command("create")
@click.argument("name")
def playlist_create(name):
    r"""
    Create a new empty playlist with the specified name.

    Examples:

        spoty spotify playlist create "My awesome playlist"
    """
    id = spoty.spotify_api.create_playlist(name)
    click.echo(f'New playlist created (id: {id}, name: "{name}")')


@playlist.command("delete")
@click.argument("playlist_ids", nargs=-1)
@click.option('--confirm', '-y', is_flag=True,
              help='Do not ask for confirmation')
def playlist_delete(playlist_ids, confirm):
    r"""
    Delete playlists.

        Examples:

        spoty spotify playlist delete 37i9dQZF1DX8z1UW9HQvSq

        spoty spotify playlist delete 37i9dQZF1DX8z1UW9HQvSq 37i9dQZF1DX7jNFrjYQurt

        spoty spotify playlist delete https://open.spotify.com/playlist/37i9dQZF1DX8z1UW9HQvSq
    """

    if len(playlist_ids) == 0:
        return

    click.echo("Found playlists: ")
    for playlist_id in playlist_ids:
        playlist = spoty.spotify_api.get_playlist(playlist_id)
        if playlist is not None:
            click.echo("  " + playlist['name'])
        else:
            click.echo(f'  Playlist {playlist_id} not found')

    if not confirm:
        click.confirm(f'Are you sure you want to delete {len(playlist_ids)} playlists?', abort=True)

    for playlist_id in playlist_ids:
        res = spoty.spotify_api.delete_playlist(playlist_id, True)
        if res:
            click.echo(f'Playlist {playlist_id} deleted')
        else:
            click.echo(f'Playlist {playlist_id} not deleted')


@playlist.command("delete-all")
@click.option('--filter-names', '--fn',
              help='List only playlists whose names matches this regex filter')
@click.option('--confirm', '-y',  is_flag=True,
              help='Do not ask for export confirmation')
def playlist_delete_all(filter_names, confirm):
    r"""
    Delete all playlists in the library.

    Examples:

        spoty spotify playlist delete-all

        spoty spotify playlist delete-all --confirm
    """

    playlists = spoty.spotify_api.get_list_of_playlists()

    if len(playlists) == 0:
        exit()

    if filter_names is not None:
        playlists = list(filter(lambda pl: re.findall(filter_names, pl['name']), playlists))
        click.echo(f'{len(playlists)} playlists matches the filter')

    if len(playlists) == 0:
        exit()

    click.echo("Found playlists: ")
    for playlist in playlists:
        click.echo(f'  {playlist["id"]} "{playlist["name"]}"')

    if not confirm:
        click.confirm(f'Are you sure you want to delete {len(playlists)} playlists?', abort=True)

    with click.progressbar(playlists, label='Deleting playlists') as bar:
        for playlist in bar:
            spoty.spotify_api.delete_playlist(playlist["id"], True)

    click.echo(f'{len(playlists)} playlist deleted')


@playlist.command("copy")
@click.argument("playlist_ids", nargs=-1)
def playlist_copy(playlist_ids):
    r"""
    Create copies of playlists.
    it could be your playlists or created by another user.
    The exact same playlists will be created in your library.

    PLAYLIST_IDS - list of playlist IDs or URIs. You can specify one ID or many IDs separated by a space.



    Examples:

        spoty spotify playlist copy 37i9dQZF1DX8z1UW9HQvSq

        spoty spotify playlist copy 37i9dQZF1DX8z1UW9HQvSq 37i9dQZF1DX7jNFrjYQurt

        spoty spotify playlist copy https://open.spotify.com/playlist/37i9dQZF1DX8z1UW9HQvSq

    """
    playlists = []
    tracks = []
    with click.progressbar(playlist_ids, label='Copying playlists') as bar:
        for playlist_id in bar:
            new_playlist_id, tracks_added = spoty.spotify_api.copy_playlist(playlist_id)
            playlists.extend(new_playlist_id)
            tracks.extend(tracks_added)

    click.echo(f'{len(playlists)} playlists with {len(tracks)} tracks copied.')


@playlist.command("add-tracks")
@click.argument("playlist_id")
@click.argument("track_ids", nargs=-1)
@click.option('--allow-duplicates', '-d', is_flag=True,
              help='Add tracks that are already in the playlist.')
def playlist_add_tracks(playlist_id, track_ids, allow_duplicates):
    r"""
    Add tracks to playlist.

    PLAYLIST_ID - playlist ID or URI.

    TRACK_IDS - list of track IDs or URIs. You can specify one ID or many IDs separated by a space.

    Examples:

        spoty spotify playlist add-tracks 37i9dQZF1DX8z1UW9HQvSq 00i9VF7sjSaTqblAuKFBDO

        spoty spotify playlist add-tracks 37i9dQZF1DX8z1UW9HQvSq 00i9VF7sjSaTqblAuKFBDO 7cjlfruK9Oqw7k5wAZGO72

        spoty spotify playlist add-tracks https://open.spotify.com/playlist/37i9dQZF1DX8z1UW9HQvSq https://open.spotify.com/track/00i9VF7sjSaTqblAuKFBDO

    """
    track_ids = list(track_ids)
    tracks_added, import_duplicates, already_exist \
        = spoty.spotify_api.add_tracks_to_playlist_by_ids(playlist_id, track_ids, allow_duplicates)
    click.echo(f'{len(tracks_added)} tracks added to playlist {playlist_id}')


@playlist.command("remove-tracks")
@click.argument("playlist_id")
@click.argument("track_ids", nargs=-1)
def playlist_remove_tracks(playlist_id, track_ids):
    r"""
    Remove tracks from playlist.

    PLAYLIST_ID - playlist ID or URI.

    TRACK_IDS - list of track IDs or URIs. You can specify one ID or many IDs separated by a space.

    Examples:

        spoty spotify playlist remove-tracks 37i9dQZF1DX8z1UW9HQvSq 00i9VF7sjSaTqblAuKFBDO

        spoty spotify playlist remove-tracks 37i9dQZF1DX8z1UW9HQvSq 00i9VF7sjSaTqblAuKFBDO 7cjlfruK9Oqw7k5wAZGO72

        spoty spotify playlist remove-tracks https://open.spotify.com/playlist/37i9dQZF1DX8z1UW9HQvSq https://open.spotify.com/track/00i9VF7sjSaTqblAuKFBDO

    """
    track_ids = list(track_ids)
    spoty.spotify_api.remove_tracks_from_playlist(playlist_id, track_ids)
    click.echo(f'Tracks removed from playlist {playlist_id}')


@playlist.command("remove-liked-tracks")
@click.argument("playlist_ids", nargs=-1)
def playlist_remove_liked_tracks(playlist_ids):
    r"""
    Read playlists and remove all liked tracks found from these playlists.

    PLAYLIST_IDS - list of playlist IDs or URIs. You can specify one ID or many IDs separated by a space.

    Examples:

        spoty spotify playlist remove-liked-tracks 37i9dQZF1DX8z1UW9HQvSq

        spoty spotify playlist remove-liked-tracks 37i9dQZF1DX8z1UW9HQvSq 37i9dQZF1DX7jNFrjYQurt

        spoty spotify playlist remove-liked-tracks https://open.spotify.com/playlist/37i9dQZF1DX8z1UW9HQvSq

    """

    all_removed_tracks = []
    with click.progressbar(playlist_ids, label='Removing liked tracks from playlists') as bar:
        for playlist_id in bar:
            removed_tracks = spoty.spotify_api.remove_liked_tracks_in_playlist(playlist_id)
            all_removed_tracks.extend(removed_tracks)

    click.echo(f'{len(all_removed_tracks)} liked tracks removed from {len(playlist_ids)} playlists.')


@playlist.command("list-invalid-tracks")
@click.argument("playlist_ids", nargs=-1)
def playlist_list_invalid_tracks(playlist_ids):
    r"""
    Read playlists and list all invalid tracks found from these playlists.
    Tracks that have no ID are considered invalid.
    If a track is not available in the given region it is not considered invalid. You can still pull information on it. Tracks that are not available for the region will not be deleted.
    Invalid tracks are those for which there is no information at all in the database (have been deleted from the spotify database).

    PLAYLIST_IDS - list of playlist IDs or URIs. You can specify one ID or many IDs separated by a space.

    Examples:

        spoty spotify playlist list-invalid-tracks 37i9dQZF1DX8z1UW9HQvSq

        spoty spotify playlist list-invalid-tracks 37i9dQZF1DX8z1UW9HQvSq 37i9dQZF1DX7jNFrjYQurt

        spoty spotify playlist list-invalid-tracks https://open.spotify.com/playlist/37i9dQZF1DX8z1UW9HQvSq

    """

    all_invalid_tracks = []
    with click.progressbar(playlist_ids, label='Collecting invalid tracks from playlists') as bar:
        for playlist_id in bar:
            removed_tracks = spoty.spotify_api.get_invalid_tracks_in_playlist(playlist_id)
            all_invalid_tracks.extend(removed_tracks)

    click.echo(f'{len(all_invalid_tracks)} invalid tracks in {len(playlist_ids)} playlists.')

    if len(all_invalid_tracks) > 0:
        for track in all_invalid_tracks:
            click.echo(str(track))


@playlist.command("like-all-tracks")
@click.argument("playlist_ids", nargs=-1)
def playlist_like_all_tracks(playlist_ids):
    r"""
    Read playlists and like all tracks in these playlists.

    PLAYLIST_IDS - list of playlist IDs or URIs. You can specify one ID or many IDs separated by a space.

    Examples:

        spoty spotify playlist like-all-tracks 37i9dQZF1DX8z1UW9HQvSq

        spoty spotify playlist like-all-tracks 37i9dQZF1DX8z1UW9HQvSq 37i9dQZF1DX7jNFrjYQurt

        spoty spotify playlist like-all-tracks https://open.spotify.com/playlist/37i9dQZF1DX8z1UW9HQvSq

    """

    all_liked_tracks = []
    with click.progressbar(playlist_ids, label='Liking all tracks in playlists') as bar:
        for playlist_id in bar:
            liked_tracks = spoty.spotify_api.like_all_tracks_in_playlist(playlist_id)
            all_liked_tracks.extend(liked_tracks)

    click.echo(f'{len(all_liked_tracks)} tracks added to liked tracks in {len(playlist_ids)} playlists.')
