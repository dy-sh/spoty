from spoty.commands.first_list_commands import \
    count_command, \
    delete_command, \
    export_command, \
    import_deezer_command, \
    import_spotify_command, \
    print_command,\
    create_m3u8_command
from spoty.commands.second_list_commands import \
    find_duplicates_second_command
from spoty.commands import filter_group
from spoty.commands.duplicates_commands import add_missing_tags_command, move_duplicates_command
from spoty.utils import SpotyContext
from spoty import settings
import click


@click.group("filter-second")
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
filter_second.add_command(create_m3u8_command.export_tracks)
filter_second.add_command(import_spotify_command.import_spotify)
filter_second.add_command(import_deezer_command.import_deezer)
filter_second.add_command(move_duplicates_command.move_duplicates)
filter_second.add_command(delete_command.delete_tracks)
filter_second.add_command(add_missing_tags_command.add_missing_tags)
filter_second.add_command(find_duplicates_second_command.find_duplicates_second)
