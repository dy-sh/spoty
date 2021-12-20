from spoty import settings
from spoty import log
import spoty.spotify
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



@playlist.command("create")
@click.argument("name", type=str)
def playlist_create(name):
    r"""
    Create a new empty playlist with the specified name.

    Examples:

        spoty playlist create "My awesome playlist"
    """
    id = spoty.spotify.create_playlist(name)
    click.echo(f'New playlist created (id: {id}, name: "{name}")')


@playlist.command("copy")
@click.argument("playlist_ids",  nargs=-1)
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
            new_playlist_id, tracks_added = spoty.spotify.copy_playlist(playlist_id)
            playlists.extend(new_playlist_id)
            tracks.extend(tracks_added)

    click.echo(f'{len(playlists)} playlists with {len(tracks)} tracks copied.')


@playlist.command("add-tracks")
@click.argument("playlist_id", type=str)
@click.argument("track_ids",  nargs=-1)
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
    tracks_added, import_duplicates, already_exist = spoty.spotify.add_tracks_to_playlist(playlist_id, track_ids, allow_duplicates)
    click.echo(f'{len(tracks_added)} tracks added to playlist {playlist_id}')


@playlist.command("remove-tracks")
@click.argument("playlist_id", type=str)
@click.argument("track_ids",  nargs=-1)
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
    spoty.spotify.remove_tracks_from_playlist(playlist_id, track_ids)
    click.echo(f'Tracks removed from playlist {playlist_id}')


@playlist.command("remove-liked-tracks")
@click.argument("playlist_ids",  nargs=-1)
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
            removed_tracks = spoty.spotify.remove_liked_tracks_in_playlist(playlist_id)
            all_removed_tracks.extend(removed_tracks)

    click.echo(f'{len(all_removed_tracks)} liked tracks removed from {len(playlist_ids)} playlists.')


@playlist.command("list-invalid-tracks")
@click.argument("playlist_ids",  nargs=-1)
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
            removed_tracks = spoty.spotify.get_invalid_tracks_in_playlist(playlist_id)
            all_invalid_tracks.extend(removed_tracks)

    click.echo(f'{len(all_invalid_tracks)} invalid tracks in {len(playlist_ids)} playlists.')

    if len(all_invalid_tracks) > 0:
        for track in all_invalid_tracks:
            click.echo(str(track))


@playlist.command("like-all-tracks")
@click.argument("playlist_ids",  nargs=-1)
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
            liked_tracks = spoty.spotify.like_all_tracks_in_playlist(playlist_id)
            all_liked_tracks.extend(liked_tracks)

    click.echo(f'{len(all_liked_tracks)} tracks added to liked tracks in {len(playlist_ids)} playlists.')
