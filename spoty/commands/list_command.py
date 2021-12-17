from spoty import settings
from spoty import log
import spoty.playlist
import spoty.like
import spoty.local
import click
import re
import spoty.utils
import time
import os
from datetime import datetime


@click.command("list")
@click.argument('src', nargs=-1)
@click.option('--ssp', '--source-spotify-playlist', multiple=True,
              help='Read tracks in specified spotify playlist.')
@click.option('--ssl', '--source-spotify-user-library', multiple=True,
              help='Read tracks in this spotify user library. If no user ID is specified, the current user will be used.')
@click.option('--sdp', '--source-deezer-playlist', multiple=True,
              help='Read tracks in specified deezer playlist.')
@click.option('--sdl', '--source-deezer-user-library', multiple=True,
              help='Read tracks in this spotify user library.')
@click.option('--slf', '--source-local-files', multiple=True,
              help='Read tracks from local files in specified path.')
@click.option('--slp', '--source-local-playlists', multiple=True,
              help='Read tracks from local csv playlists in specified path.')
@click.option('--fn', '--filter-source-names', multiple=True,
              help='Read only files/playlists whose names matches this regex filter')
@click.option('--ft', '--filter-source-tags', multiple=True,
              help='Get only tracks that have all of the specified tags.')
@click.option('--fn', '--filter-source-no-tags', multiple=True,
              help='Get only tracks that do not have any of the listed tags.')
@click.option('-r', '--recursive', is_flag=True,
              help='Search in subdirectories from the specified path.')
@click.option('-c', '--count', is_flag=True,
              help='Print number of tracks read to console.')
@click.option('-p', '--print', is_flag=True,
              help='Print a list of read tracks to console.')
@click.option('--s', '--save',
              help='Save a list of read tracks to csv playlists.')
@click.option('--ms', '--merge-save',
              help='Save a list of read tracks to one merged csv playlist.')
@click.option('-o', '--overwrite', is_flag=True,
              help='Overwrite existing csv playlists without asking')
@click.option('-t', '--timestamp', is_flag=True,
              help='Create a new subfolder with the current date and time for saved csv playlists')
def list(src, ssp, ssl, sdp, sdl, slf, slp, fn, ft, recursive, count, print, s, ms, overwrite, timestamp):
    r"""
    List of tracks.

    \b
    SRC - List of local files paths or music services URIs.
    This argument is optional. Instead, you can pass parameters as --source options.
    Unlike --source options, the SRC argument accepts only the path to local files or the full URI to playlist.
    The --source options can also accept the ID of the playlist on a music service.

    Examples:
        ploty list -c https://open.spotify.com/playlist/7E6SNhIGjSqEmzHISqnMrJ https://open.spotify.com/playlist/7E45634fjSqEmzHISqnMrJ

        ploty list -c --ssp 0yRgrCdkntJG83mFbFvrBP --ssp https://open.spotify.com/playlist/7E6SNhIGjSqEmzHISqnMrJ

    """

    ssp_list=[]
    ssp_list.extend(ssp)

    slf_list = []
    slf_list.extend(slf)

    for source in src:
        if spoty.utils.check_is_playlist_URI(source):
            ssp_list.append(source)
        elif spoty.local.is_valid_path(source):
            slf_list.extend(source)
        else:
            click.echo(f'Cant recognize source: "{source}"', err=True)

    source_spotify_tracks = []
    source_spotify_tracks_tags = []
    all_source_tracks_tags = []
    with click.progressbar(ssp_list, label='Reading spotify playlists') as bar:
        for playlist_id in bar:
            tracks = spoty.playlist.get_tracks_of_playlist(playlist_id)
            source_spotify_tracks.extend(tracks)
            tags = spoty.utils.read_tags_from_spotify_tracks(tracks)
            all_source_tracks_tags.extend(tags)
            source_spotify_tracks_tags.extend(tags)

    if count:
        click.echo(f'Total tracks: {len(all_source_tracks_tags)}')

    if print:
        for i, track in enumerate(source_spotify_tracks_tags):
            click.echo(
                f'--------------------- SPOTIFY TRACK {i + 1} / {len(source_spotify_tracks_tags)} ---------------------')
            spoty.utils.print_track_main_tags(track)
