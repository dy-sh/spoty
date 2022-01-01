from spoty.commands.duplicates_commands import \
    add_missing_tags_command, \
    replace_tags_command, \
    delete_duplicates_command, \
    export_duplicates_command, \
    move_duplicates_command, \
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


@click.group("duplicates")
@click.option('--compare-tags-def', '--ctd', show_default=True, multiple=True,
              default=settings.SPOTY.COMPARE_TAGS_DEFINITELY_DUPLICATE,
              help='Compare definitely duplicates by this tags. It is optional. You can also change the list of tags in the config file.')
@click.option('--compare-tags-prob', '--ctp', show_default=True, multiple=True,
              default=settings.SPOTY.COMPARE_TAGS_PROBABLY_DUPLICATE,
              help='Compare probably duplicates by this tags. It is optional. You can also change the list of tags in the config file.')
@click.option('--only-def', '--od', '-d', is_flag=True,
              help='Find only definitely duplicates.')
@click.option('--only-prob', '--op', '-p', is_flag=True,
              help='Find only probably duplicates.')
@click.pass_obj
def find_duplicates_second(context: SpotyContext,
                           compare_tags_def,
                           compare_tags_prob,
                           only_def,
                           only_prob
                           ):
    """
Find duplicates between the first and second list of tracks.
    """

    if only_def and only_prob:
        click.echo(f'Simultaneous use of "--only-def" and "--only-prob" is not possible', err=True)
        exit()

    source_list = context.tags_lists[0]
    dest_list = context.tags_lists[1]

    compare_tags_def = spoty.utils.tuple_to_list(compare_tags_def)
    compare_tags_prob = spoty.utils.tuple_to_list(compare_tags_prob)

    if only_def:
        compare_tags_prob = []
    if only_prob:
        compare_tags_def = []

    duplicates_groups, unique_source_tracks, unique_dest_tracks,sources_def_dups, sources_prob_dups = \
        spoty.utils.find_duplicates_in_tag_lists(source_list, dest_list, compare_tags_def, compare_tags_prob,
                                                 True,True)

    context.duplicates_groups = duplicates_groups
    context.unique_first_tracks = unique_source_tracks
    context.unique_second_tracks = unique_dest_tracks

    total_def_duplicates_count = 0
    total_prob_duplicates_count = 0

    for group in context.duplicates_groups:
        total_def_duplicates_count += len(group.def_duplicates)
        total_prob_duplicates_count += len(group.prob_duplicates)

    context.summary.append("Finding duplicates:")
    if len(unique_source_tracks) > 0:
        context.summary.append(f'  {len(unique_source_tracks)} unique tracks is first list found.')
    if len(sources_def_dups) > 0:
        context.summary.append(f'  {len(sources_def_dups)} definitely duplicates is first list found.')
    if len(sources_prob_dups) > 0:
        context.summary.append(f'  {len(sources_prob_dups)} probably duplicates is first list found.')
    if len(unique_dest_tracks) > 0:
        context.summary.append(f'  {len(unique_dest_tracks)} unique tracks is second list found.')
    if total_def_duplicates_count > 0:
        context.summary.append(f'  {total_def_duplicates_count} definitely duplicates in second list found.')
    if total_prob_duplicates_count > 0:
        context.summary.append(f'  {total_prob_duplicates_count} probably duplicates in second list found.')


    if total_def_duplicates_count == 0 and total_prob_duplicates_count == 0:
        context.summary.append(f'  0 duplicates found.')


find_duplicates_second.add_command(add_missing_tags_command.add_missing_tags)
find_duplicates_second.add_command(replace_tags_command.replace_tags)
find_duplicates_second.add_command(delete_duplicates_command.delete_duplicates)
find_duplicates_second.add_command(export_duplicates_command.export_duplicates)
find_duplicates_second.add_command(move_duplicates_command.move_duplicates)
find_duplicates_second.add_command(print_duplicates_command.print_duplicates)
find_duplicates_second.add_command(get_duplicates_group.get_duplicates)
find_duplicates_second.add_command(get_unique_group.get_unique)
