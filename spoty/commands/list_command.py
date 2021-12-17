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
@click.option('--ssp','--source-spotify-playlist', multiple=True,
              help='Read tracks in specified spotify playlist.')
@click.option('--ssl','--source-spotify-user-library', multiple=True,
              help='Read tracks in this spotify user library. If no user ID is specified, the current user will be used.')
@click.option('--sdp','--source-deezer-playlist', multiple=True,
              help='Read tracks in specified deezer playlist.')
@click.option('--sdl','--source-deezer-user-library', multiple=True,
              help='Read tracks in this spotify user library.')
@click.option('--slf','--source-local-files', multiple=True,
              help='Read tracks from local files in specified path.')
@click.option('--slp','--source-local-playlists', multiple=True,
              help='Read tracks from local csv playlists in specified path.')
@click.option('--fn','--filter-source-names', multiple=True,
              help='Read only files/playlists whose names matches this regex filter')
@click.option('--ft','--filter-source-tags', multiple=True,
              help='Get only tracks that have all of the specified tags.')
@click.option('--fn','--filter-source-no-tags', multiple=True,
              help='Get only tracks that do not have any of the listed tags.')
@click.option('-r', '--recursive',  is_flag=True,
              help='Search in subdirectories from the specified path.')
@click.option('-c','--count',is_flag=True,
              help='Print number of tracks read to console.')
@click.option('-p','--print',is_flag=True,
              help='Print a list of read tracks to console.')
@click.option('--s','--save',
              help='Save a list of read tracks to csv playlists.')
def list(ssp, ssl, sdp, sdl, slf, slp, fn, ft, recursive, count, print, s):
    r"""
    List of all playlists.

    Examples:

    """
    source_tracks=[]
    for playlist_id in ssp:
        tracks = spoty.playlist.get_tracks_of_playlist(playlist_id)
        source_tracks.extend(tracks)


    click.echo(f'Total tracks: {len(source_tracks)}')


