from spoty import settings
from spoty import log
import spoty.deezer_api
import spoty.csv_playlist
import spoty.deezer_api
import spoty.spotify_api
import spoty.utils
from spoty.commands import get_group
from spoty.utils import SpotyContext
import click
import os
from datetime import datetime


@click.command("compare")
@click.option('--result-path', '--rp',
              default=settings.SPOTY.DEFAULT_LIBRARY_PATH,
              help='Path to create resulting csv files')
@click.option('--grouping-pattern', '--gp', show_default=True,
              default=settings.SPOTY.DEFAULT_GROUPING_PATTERN,
              help='Tracks will be grouped to playlists according to this pattern.')
@click.pass_obj
def compare(context: SpotyContext,
            result_path,
            grouping_pattern
            ):
    """
Compare tracks on two lists and export the result (unique tracks, duplicates) to csv files.
    """

    source_list = context.tags_lists[0]
    dest_list = context.tags_lists[1]

    source_unique, dest_unique, source_def_dups, dest_def_dups, source_prob_dups, dest_prob_dups = \
        spoty.utils.compare_tags_lists(source_list, dest_list, True)

    # export result to  csv files
    result_path = os.path.abspath(result_path)
    date_time_str = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    result_path = os.path.join(result_path, 'compare-' + date_time_str)

    if len(dest_def_dups) > 0:
        spoty.csv_playlist.create_csvs(dest_def_dups, os.path.join(result_path, 'dest_definitely_duplicates'),
                                       grouping_pattern)
    if len(dest_prob_dups) > 0:
        spoty.csv_playlist.create_csvs(dest_prob_dups, os.path.join(result_path, 'dest_probably_duplicates'),
                                       grouping_pattern)
    if len(dest_unique) > 0:
        spoty.csv_playlist.create_csvs(dest_unique, os.path.join(result_path, 'dest_unique'), grouping_pattern)
    if len(source_def_dups) > 0:
        spoty.csv_playlist.create_csvs(source_def_dups, os.path.join(result_path, 'source_definitely_duplicates'),
                                       grouping_pattern)
    if len(source_prob_dups) > 0:
        spoty.csv_playlist.create_csvs(source_prob_dups, os.path.join(result_path, 'source_probably_duplicates'),
                                       grouping_pattern)
    if len(source_unique) > 0:
        spoty.csv_playlist.create_csvs(source_unique, os.path.join(result_path, 'source_unique'), grouping_pattern)
