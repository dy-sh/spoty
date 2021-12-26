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
              default=settings.SPOTY.DEFAULT_EXPORT_PATH,
              help='Path to create resulting csv files')
@click.option('--grouping-pattern', '--gp', show_default=True,
              default=settings.SPOTY.DEFAULT_GROUPING_PATTERN,
              help='Tracks will be grouped to playlists according to this pattern.')
@click.option('--compare-tags-def', '--ctd', show_default=True, multiple=True,
              default=settings.SPOTY.COMPARE_TAGS_DEFINITELY_DUPLICATE,
              help='Compare definitely duplicates by this tags. It is optional. You can also change the list of tags in the config file.')
@click.option('--compare-tags-prob', '--ctp', show_default=True, multiple=True,
              default=settings.SPOTY.COMPARE_TAGS_PROBABLY_DUPLICATE,
              help='Compare probably duplicates by this tags. It is optional. You can also change the list of tags in the config file.')
@click.pass_obj
def compare(context: SpotyContext,
            result_path,
            grouping_pattern,
            compare_tags_def,
            compare_tags_prob,
            ):
    """
Compare tracks on two lists and export the result (unique tracks, duplicates) to csv files.
    """

    source_list = context.tags_lists[0]
    dest_list = context.tags_lists[1]

    compare_tags_def = spoty.utils.tuple_to_list(compare_tags_def)
    compare_tags_prob = spoty.utils.tuple_to_list(compare_tags_prob)

    source_unique, dest_unique, source_def_dups, dest_def_dups, source_prob_dups, dest_prob_dups = \
        spoty.utils.find_duplicates_in_tag_lists(source_list, dest_list, compare_tags_def, compare_tags_prob, True)

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
