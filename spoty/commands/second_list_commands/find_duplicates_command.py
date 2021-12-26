from spoty.commands.duplicates_commands import \
    add_missing_tags_command, \
    compare_command, \
    delete_duplicates_command, \
    export_duplicates_command, \
    move_duplicates_command, \
    print_duplicates_command
from spoty.utils import SpotyContext
from spoty import settings
from spoty import log
import spoty.deezer_api
import spoty.csv_playlist
import spoty.deezer_api
import spoty.spotify_api
import spoty.audio_files
import spoty.utils
import click
import os
from datetime import datetime


@click.group("duplicates")
@click.option('--compare-tags-def', '--ctd', show_default=True, multiple=True,
              default=settings.SPOTY.COMPARE_TAGS_DEFINITELY_DUPLICATE,
              help='Compare definitely duplicates by this tags. It is optional. You can also change the list of tags in the config file.')
@click.option('--compare-tags-prob', '--ctp', show_default=True, multiple=True,
              default=settings.SPOTY.COMPARE_TAGS_PROBABLY_DUPLICATE,
              help='Compare probably duplicates by this tags. It is optional. You can also change the list of tags in the config file.')
@click.option('--no-prob', '-p', is_flag=True,
              help='Do not include probably duplicates')
@click.pass_obj
def find_duplicates(context: SpotyContext,
                    compare_tags_def,
                    compare_tags_prob,
                    no_prob,
                    ):
    """
Find duplicates between the first and second list of tracks.
    """

    source_list = context.tags_lists[0]
    dest_list = context.tags_lists[1]

    compare_tags_def = spoty.utils.tuple_to_list(compare_tags_def)
    compare_tags_prob = spoty.utils.tuple_to_list(compare_tags_prob)

    if no_prob:
        compare_tags_prob = []

    duplicates_groups, unique_source_tracks, unique_dest_tracks = \
        spoty.utils.find_duplicates_in_tag_lists_grouped(source_list, dest_list, compare_tags_def, compare_tags_prob,
                                                         True)

    context.duplicates_groups = duplicates_groups
    context.unique_source_tracks = unique_source_tracks
    context.unique_dest_tracks = unique_dest_tracks

    total_source_def_duplicates_count = 0
    total_dest_def_duplicates_count = 0
    total_source_prob_duplicates_count = 0
    total_dest_prob_duplicates_count = 0

    for group in context.duplicates_groups:
        total_source_def_duplicates_count += len(group.source_def_duplicates) - 1
        total_dest_def_duplicates_count += len(group.dest_def_duplicates)
        total_source_prob_duplicates_count += len(group.source_prob_duplicates)
        total_dest_prob_duplicates_count += len(group.dest_prob_duplicates)

    context.summary.append("Finding duplicates:")
    if total_source_def_duplicates_count > 0:
        context.summary.append(f'  {total_source_def_duplicates_count} definitely duplicates in source list')
    if total_source_prob_duplicates_count > 0:
        context.summary.append(f'  {total_source_prob_duplicates_count} probably duplicates in source list')
    if total_dest_def_duplicates_count > 0:
        context.summary.append(f'  {total_dest_def_duplicates_count} definitely duplicates in destination list')
    if total_dest_prob_duplicates_count > 0:
        context.summary.append(f'  {total_dest_prob_duplicates_count} probably duplicates in destination list')


# find_duplicates.add_command(add_missing_tags_command.add_missing_tags)
# find_duplicates.add_command(compare_command.compare)
# find_duplicates.add_command(delete_duplicates_command.delete_duplicates)
find_duplicates.add_command(export_duplicates_command.export_duplicates)
# find_duplicates.add_command(move_duplicates_command.move_duplicates)
find_duplicates.add_command(print_duplicates_command.print_duplicates)
