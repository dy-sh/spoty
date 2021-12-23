from spoty import settings
from spoty import log
import spoty.deezer_api
import spoty.csv_playlist
import spoty.deezer_api
import spoty.spotify_api
import spoty.utils
from spoty.commands import get_group
from spoty.utils import SpotyContext
from spoty.utils import FakeContext
import click
import os
from datetime import datetime


@click.command("compare")
@click.option('--spotify-playlist', '--sp', multiple=True,
              help='Get tracks from Spotify playlist URI or ID.')
@click.option('--spotify-entire-library', '--s', multiple=True,
              help='Get all tracks from Spotify library (by user URI or ID). To request a list for the current authorized user, use "me" as ID.')
@click.option('--spotify-entire-library-regex', '--sr', nargs=2, multiple=True,
              help='Works the same as --spotify-entire-library, but you can specify regex filter which will be applied to playlists names. This way you can query any playlists by names.')
@click.option('--deezer-playlist', '--dp', multiple=True,
              help='Get tracks from Deezer playlist URI or ID.')
@click.option('--deezer-entire-library', '--d', multiple=True,
              help='Get all tracks from Deezer library (by user URI or ID). To request a list for the current authorized user, use "me" as ID.')
@click.option('--deezer-entire-library-regex', '--dr', nargs=2, multiple=True,
              help='Works the same as --deezer-entire-library, but you can specify regex filter which will be applied to playlists names. This way you can query any playlists by names.')
@click.option('--audio', '--a', multiple=True,
              help='Get audio files located at the specified local path. You can specify the audio file name as well.')
@click.option('--csv', '--c', multiple=True,
              help='Get tracks from csv playlists located at the specified local path. You can specify the scv file name as well.')
@click.option('--no-recursive', '-r', is_flag=True,
              help='Do not search in subdirectories from the specified path.')
@click.option('--result-path', '--rp',
              default=settings.SPOTY.DEFAULT_LIBRARY_PATH,
              help='Path to create resulting csv files')
@click.pass_obj
def compare(context: SpotyContext,
            spotify_playlist,
            spotify_entire_library,
            spotify_entire_library_regex,
            deezer_playlist,
            deezer_entire_library,
            deezer_entire_library_regex,
            audio,
            csv,
            no_recursive,
            result_path
            ):
    """
Compare tracks on two sources (missing tracks, duplicates) to csv files.
Add another source with this command options.
    """

    context2 = FakeContext()
    get_group.get_tracks_wrapper(context2,
               spotify_playlist,
               spotify_entire_library,
               spotify_entire_library_regex,
               deezer_playlist,
               deezer_entire_library,
               deezer_entire_library_regex,
               audio,
               csv,
               no_recursive,
               )

    tags_list1 = context.tags_list
    tags_list2 = context2.obj.tags_list

    tags_to_compare=[spoty.deezer_api.DEEZER_TRACK_ID_TAG,]

    tags_list1 = spoty.utils.remove_tags_duplicates(tags_list1)
