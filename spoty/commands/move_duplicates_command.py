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


@click.command("move-duplicates")
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
@click.option('--grouping-pattern', '--gp', show_default=True,
              default=settings.SPOTY.DEFAULT_GROUPING_PATTERN,
              help='Tracks will be grouped to playlists according to this pattern.')
@click.option('--move-unique', '-u', is_flag=True,
              help='Move unique files too (to a separate folder).')
@click.option('--move-source', '-s', is_flag=True,
              help='Move source files too (to a separate folder).')
@click.pass_obj
def move_duplicates(context: SpotyContext,
                    spotify_playlist,
                    spotify_entire_library,
                    spotify_entire_library_regex,
                    deezer_playlist,
                    deezer_entire_library,
                    deezer_entire_library_regex,
                    audio,
                    csv,
                    no_recursive,
                    result_path,
                    grouping_pattern,
                    move_unique,
                    move_source
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

    source_list = context.tags_list
    dest_list = context2.obj.tags_list

    source_unique, dest_unique, source_def_dups, dest_def_dups, source_prob_dups, dest_prob_dups = \
        spoty.utils.compare_tags_lists(source_list, dest_list, True)

    # export result to  csv files
    result_path = os.path.abspath(result_path)
    date_time_str = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    result_path = os.path.join(result_path, 'move-duplicates-' + date_time_str)

    move_files(dest_def_dups, os.path.join(result_path, 'dest_definitely_duplicates'), grouping_pattern)
    move_files(dest_prob_dups, os.path.join(result_path, 'dest_probably_duplicates'), grouping_pattern)
    if move_unique:
        move_files(dest_unique, os.path.join(result_path, 'dest_unique'), grouping_pattern)
    if move_source:
        move_files(source_def_dups, os.path.join(result_path, 'source_definitely_duplicates'), grouping_pattern)
        move_files(source_prob_dups, os.path.join(result_path, 'source_probably_duplicates'), grouping_pattern)
        if move_unique:
            move_files(source_unique, os.path.join(result_path, 'source_unique'), grouping_pattern)


def move_files(tags_list, path, grouping_pattern):
    if len(tags_list) > 0:
        grouped_tags = spoty.utils.group_tags_by_pattern(tags_list, grouping_pattern)

        for group, tags_l in grouped_tags.items():
            group_path = os.path.join(path, group)
            os.makedirs(group_path, exist_ok=True)
            for tags in tags_list:
                file_name = tags['SPOTY_FILE_NAME']
                new_file_name = os.path.join(group_path, os.path.basename(file_name))
                os.rename(file_name, new_file_name)
