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
from spoty.utils import SpotyContext


@click.group("filter")
# @click.option('--playlist-names', '--p', multiple=True,
#               help='Leave only playlists whose names matches this regex filter')
@click.option('--have-tags', '--t', multiple=True,
              help='Leave only tracks that have all of the specified tags.')
@click.option('--have-no-tags', '--nt', multiple=True,
              help='Leave only tracks that do not have any of the specified tags.')
@click.option('--duplicates', '-d', type=bool, is_flag=True, default=False,
              help='Remove duplicates.')
@click.option('--duplicates-compare-tags', '--dt', show_default=True,
              default=settings.SPOTY.DEFAULT_COMPARE_TAGS,
              help='Compare duplicates by this tags. It is optional. You can also change the list of tags in the config file.')
@click.pass_obj
def filter_tracks(context: SpotyContext,
                  # playlist_names,
                  have_tags,
                  have_no_tags,
                  duplicates,
                  duplicates_compare_tags
                  ):
    """
Filter tracks.
    """

    tags_list = context.tags_list

    if len(tags_list) > 0:
        if len(have_tags) > 0:
            new_tags_list = spoty.utils.filter_tags_list_have_tags(tags_list, have_tags)

            if len(tags_list) - len(new_tags_list)  != 0:
                context.summary += f'{len(tags_list) - len(new_tags_list)} tracks filtered (that have all of the specified tags).'
            tags_list = new_tags_list


        if len(have_no_tags) > 0:
            new_tags_list = spoty.utils.filter_tags_list_have_no_tags(tags_list, have_no_tags)

            if len(tags_list) - len(new_tags_list)  != 0:
                context.summary += f'{len(tags_list) - len(new_tags_list)} tracks filtered (that do not have any of the specified tags).'
            tags_list = new_tags_list

        a=['123','12312321313123','123123123123213']
        if duplicates:
            new_tags_list, dup = spoty.utils.remove_tags_duplicates(tags_list, duplicates_compare_tags, True)
            if len(dup) > 0:
                context.summary += f'{len(dup)} duplicates found in {len(tags_list)} tracks'
            tags_list = new_tags_list

    context.tags_list = tags_list


filter_tracks.add_command(transfer_command.transfer)
