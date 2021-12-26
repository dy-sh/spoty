from spoty.commands import count_command
from spoty.commands import print_command
from spoty.commands import export_command
from spoty.commands import import_spotify_command
from spoty.commands import import_deezer_command
from spoty.commands import compare_command
from spoty.commands import move_duplicates_command
from spoty.commands import filter_group
from spoty.commands import delete_command
from spoty.commands import add_missing_tags_command
from spoty.utils import SpotyContext
from spoty import settings
from spoty import log
import spoty.utils
import click


@click.group("filter-second")
# @click.option('--playlist-names', '--p', multiple=True,
#               help='Leave only playlists whose names matches this regex filter')
@click.option('--leave-have-tags', '--lht', multiple=True,
              help='Leave only tracks that have all of the specified tags.')
@click.option('--leave-no-tags', '--lnt', multiple=True,
              help='Leave only tracks that do not have any of the specified tags.')
@click.option('--remove-duplicates', '--rd', '-d', type=bool, is_flag=True, default=False,
              help='Remove duplicates.')
@click.option('--leave-duplicates', '--ld', '-l', type=bool, is_flag=True, default=False,
              help='Leave only duplicates.')
@click.option('--duplicates-compare-tags', '--dct', show_default=True, multiple=True,
              default=settings.SPOTY.COMPARE_TAGS_DEFINITELY_DUPLICATE,
              help='Compare duplicates by this tags. It is optional. You can also change the list of tags in the config file.')
@click.pass_obj
def filter_second(context: SpotyContext,
                  # playlist_names,
                  leave_have_tags,
                  leave_no_tags,
                  remove_duplicates,
                  leave_duplicates,
                  duplicates_compare_tags
                  ):
    """
Filter tracks.
    """

    filter_group.filter_tracks_wrapper(context,
                                       # playlist_names,
                                       leave_have_tags,
                                       leave_no_tags,
                                       remove_duplicates,
                                       leave_duplicates,
                                       duplicates_compare_tags
                                       )

filter_second.add_command(count_command.count_tracks)
filter_second.add_command(print_command.print_tracks)
filter_second.add_command(export_command.export_tracks)
filter_second.add_command(import_spotify_command.import_spotify)
filter_second.add_command(import_deezer_command.import_deezer)
filter_second.add_command(compare_command.compare)
filter_second.add_command(move_duplicates_command.move_duplicates)
filter_second.add_command(delete_command.delete_tracks)
filter_second.add_command(add_missing_tags_command.add_missing_tags)

