from spoty import settings
from spoty import log
import spoty.deezer_api
import spoty.csv_playlist
import spoty.deezer_api
import spoty.spotify_api
import spoty.audio_files
import spoty.utils
from spoty.commands import get_group
from spoty.utils import SpotyContext
import click
import os
from datetime import datetime


@click.command("duplicates")
@click.option('--compare-tags-def', '--ctd', show_default=True, multiple=True,
              default=settings.SPOTY.COMPARE_TAGS_DEFINITELY_DUPLICATE,
              help='Compare definitely duplicates by this tags. It is optional. You can also change the list of tags in the config file.')
@click.option('--compare-tags-prob', '--ctp', show_default=True, multiple=True,
              default=settings.SPOTY.COMPARE_TAGS_PROBABLY_DUPLICATE,
              help='Compare probably duplicates by this tags. It is optional. You can also change the list of tags in the config file.')
@click.pass_obj
def find_duplicates(context: SpotyContext,
                    compare_tags_def,
                    compare_tags_prob,
                    ):
    """
Find duplicates between the first and second list of tracks.
    """

    source_list = context.tags_lists[0]
    dest_list = context.tags_lists[1]

    compare_tags_def = spoty.utils.tuple_to_list(compare_tags_def)
    compare_tags_prob = spoty.utils.tuple_to_list(compare_tags_prob)

    duplicates_groups = \
        spoty.utils.compare_tags_lists_grouped(source_list, dest_list, compare_tags_def, compare_tags_prob, False)

    context.duplicates_groups = duplicates_groups
