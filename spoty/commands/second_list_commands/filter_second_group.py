from spoty.commands.first_list_commands import \
    count_command, \
    export_command, \
    print_command, \
    filter_group
from spoty.commands.second_list_commands import \
    find_duplicates_second_command,\
    find_deezer_second_group,\
    find_spotify_second_group
from spoty.utils import SpotyContext
from spoty import settings
import click


@click.group("filter")
# @click.option('--playlist-names', '--p', multiple=True,
#               help='Leave only playlists whose names matches this regex filter')
@click.option('--leave-have-tags', '--lht', multiple=True,
              help='Leave only tracks that have all of the specified tags.')
@click.option('--leave-no-tags', '--lnt', multiple=True,
              help='Leave only tracks that do not have any of the specified tags.')
@click.option('--remove-duplicates', '--rd', '-d', is_flag=True,
              help='Remove duplicates.')
@click.option('--leave-duplicates', '--ld', '-l', is_flag=True,
              help='Leave only duplicates.')
@click.option('--duplicates-compare-tags', '--dct', show_default=True, multiple=True,
              default=settings.SPOTY.COMPARE_TAGS_DEFINITELY_DUPLICATE,
              help='Compare duplicates by this tags. It is optional. You can also change the list of tags in the config file.')
@click.option('--leave-added-before', '--lab',
              help='Leave only added to playlist before specified date.')
@click.option('--leave-added-after', '--laa',
              help='Leave only added to playlist after specified date.')
@click.pass_obj
def filter_second(context: SpotyContext,
                  # playlist_names,
                  leave_have_tags,
                  leave_no_tags,
                  remove_duplicates,
                  leave_duplicates,
                  duplicates_compare_tags,
    leave_added_before,
    leave_added_after,
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
                                       duplicates_compare_tags,
                                       leave_added_before,
                                       leave_added_after,
                                       )


filter_second.add_command(count_command.count_tracks)
filter_second.add_command(print_command.print_tracks)
filter_second.add_command(export_command.export_tracks)
filter_second.add_command(find_duplicates_second_command.find_duplicates_second)
filter_second.add_command(find_deezer_second_group.find_deezer)
filter_second.add_command(find_spotify_second_group.find_spotify)
