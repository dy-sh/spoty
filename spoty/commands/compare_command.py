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

    tags_to_compare = \
        [
            'DEEZER_TRACK_ID',
            'SPOTIFY_TRACK_ID',
            'ISRC',
            'ARTIST,TITLE,SPOTY_LENGTH'
        ]

    for i, tags in enumerate(tags_to_compare):
        tags_to_compare[i] = tags.split(',')

    all_tags_list1_dup = []
    all_tags_list2_dup = []
    for tags in tags_to_compare:
        tags_list1, dup = spoty.utils.remove_tags_duplicates(tags_list1, tags, False)
        all_tags_list1_dup.extend(dup)
        tags_list2, dup = spoty.utils.remove_tags_duplicates(tags_list2, tags, False)
        all_tags_list2_dup.extend(dup)

    all_new1 = {}
    all_new2 = {}
    for i, tags in enumerate(tags_list1):
        tags_list1[i]['SPOTY_TEMP_ID'] = i
        all_new1[i] = tags_list1[i]

    for i, tags in enumerate(tags_list2):
        tags_list2[i]['SPOTY_TEMP_ID'] = i
        all_new2[i] = tags_list2[i]


    all_exist1 = {}
    all_exist2 = {}
    for tags in tags_to_compare:
        compare_by_tags(tags_list1, tags_list2, tags, all_new2, all_exist2)
        compare_by_tags(tags_list2, tags_list1, tags, all_new1, all_exist1)

    print()

def compare_by_tags(tags_list1,tags_list2, tags, all_new2, all_exist2 ):
    new, exist = spoty.utils.remove_exist_tags(tags_list1, tags_list2, tags, False)
    for item in exist:
        if not 'SPOTY_TEMP_DUPLICATE_BY_TAGS' in item:
            item['SPOTY_TEMP_DUPLICATE_BY_TAGS'] = []

        item['SPOTY_TEMP_DUPLICATE_BY_TAGS'].append(tags)

        id = item['SPOTY_TEMP_ID']
        if id in all_new2:
            all_exist2[id] = item
            del all_new2[id]