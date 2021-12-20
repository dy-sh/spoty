from spoty import settings
from spoty import log
import spoty.spotify
import spoty.audio_files
import spoty.csv_playlist
import spoty.utils
import click
import re
import time
import os
from datetime import datetime
from spoty.commands import transfer_command

@click.group("filter")
@click.option('--playlist-names', '--fpn',
              help='Read only playlists whose names matches this regex filter')
@click.option('--have-tags', '--fht', multiple=True,
              help='Get only tracks that have all of the specified tags.')
@click.option('--have-no-tags', '--fhnt', multiple=True,
              help='Get only tracks that do not have any of the listed tags.')
@click.pass_context
def filter_tracks(ctx,
        playlist_names,
        have_tags,
        have_no_tags,
        ):
    """

    """
    pass

    # if len(filter_have_tags) > 0:
    #     tracks = filter_spotify_tracks_which_have_all_tags(tracks, filter_have_tags)
    #
    # if len(filter_have_no_tags) > 0:
    #     tracks = filter_spotify_tracks_which_not_have_any_of_tags(tracks, filter_have_no_tags)


filter_tracks.add_command(transfer_command.transfer)