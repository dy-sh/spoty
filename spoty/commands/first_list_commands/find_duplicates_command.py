from spoty.commands.duplicates_commands import \
    add_missing_tags_command, \
    export_duplicates_command, \
    print_duplicates_command, \
    get_duplicates_group, \
    get_unique_group
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


@click.group("dup")
@click.option('--compare-tags-def', '--ctd', show_default=True, multiple=True,
              default=settings.SPOTY.COMPARE_TAGS_DEFINITELY_DUPLICATE,
              help='Compare definitely duplicates by this tags. It is optional. You can also change the list of tags in the config file.')
@click.option('--compare-tags-prob', '--ctp', show_default=True, multiple=True,
              default=settings.SPOTY.COMPARE_TAGS_PROBABLY_DUPLICATE,
              help='Compare probably duplicates by this tags. It is optional. You can also change the list of tags in the config file.')
@click.option('--only-def', '--def', '-d', is_flag=True,
              help='Find only definitely duplicates.')
@click.option('--only-prob', '--prob', '-p', is_flag=True,
              help='Find only probably duplicates.')
@click.pass_obj
def find_duplicates(context: SpotyContext,
                    compare_tags_def,
                    compare_tags_prob,
                    only_def,
                    only_prob
                    ):
    """
Find duplicates.
    """

    tags_list = context.tags_lists[0]

    compare_tags_def = spoty.utils.tuple_to_list(compare_tags_def)
    compare_tags_prob = spoty.utils.tuple_to_list(compare_tags_prob)

    if only_def:
        compare_tags_prob = []
    if only_prob:
        compare_tags_def = []

    duplicates_groups, unique_tracks = spoty.utils.find_duplicates_in_tag_list2(tags_list, compare_tags_def,
                                                                                compare_tags_prob, True)

    context.duplicates_groups = duplicates_groups
    context.unique_first_tracks = unique_tracks

    total_def_duplicates_count = 0
    total_prob_duplicates_count = 0

    for group in context.duplicates_groups:
        total_def_duplicates_count += len(group.def_duplicates)
        total_prob_duplicates_count += len(group.prob_duplicates)

    context.summary.append("Finding duplicates:")
    if total_def_duplicates_count > 0:
        context.summary.append(f'  {total_def_duplicates_count} definitely duplicates found')
    if total_prob_duplicates_count > 0:
        context.summary.append(f'  {total_prob_duplicates_count} probably duplicates found')


find_duplicates.add_command(add_missing_tags_command.add_missing_tags)
find_duplicates.add_command(export_duplicates_command.export_duplicates)
find_duplicates.add_command(print_duplicates_command.print_duplicates)
find_duplicates.add_command(get_duplicates_group.get_duplicates)
find_duplicates.add_command(get_unique_group.get_unique)