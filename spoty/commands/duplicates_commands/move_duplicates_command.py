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


@click.command("move-duplicates")
@click.option('--result-path', '--rp',
              default=settings.SPOTY.DEFAULT_EXPORT_PATH,
              help='Path to create resulting csv files')
@click.option('--grouping-pattern', '--gp', show_default=True,
              default=settings.SPOTY.DEFAULT_GROUPING_PATTERN,
              help='Tracks will be grouped to playlists according to this pattern.')
@click.option('--move-unique', '-u', is_flag=True,
              help='Move unique files too (to a separate folder).')
@click.option('--move-source', '-s', is_flag=True,
              help='Move source files too (to a separate folder).')
@click.option('--compare-tags-def', '--ctd', show_default=True, multiple=True,
              default=settings.SPOTY.COMPARE_TAGS_DEFINITELY_DUPLICATE,
              help='Compare definitely duplicates by this tags. It is optional. You can also change the list of tags in the config file.')
@click.option('--compare-tags-prob', '--ctp', show_default=True, multiple=True,
              default=settings.SPOTY.COMPARE_TAGS_PROBABLY_DUPLICATE,
              help='Compare probably duplicates by this tags. It is optional. You can also change the list of tags in the config file.')
@click.pass_obj
def move_duplicates(context: SpotyContext,
                    result_path,
                    grouping_pattern,
                    move_unique,
                    move_source,
                    compare_tags_def,
                    compare_tags_prob,
                    ):
    """
Compare the tracks in two lists and move duplicated audio files to a new folder.
    """

    source_list = context.tags_lists[0]
    dest_list = context.tags_lists[1]

    compare_tags_def = spoty.utils.tuple_to_list(compare_tags_def)
    compare_tags_prob = spoty.utils.tuple_to_list(compare_tags_prob)

    source_unique, dest_unique, source_def_dups, dest_def_dups, source_prob_dups, dest_prob_dups = \
        spoty.utils.compare_tags_lists(source_list, dest_list, compare_tags_def, compare_tags_prob, True)

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
