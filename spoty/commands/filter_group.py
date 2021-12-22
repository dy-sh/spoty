from spoty.commands import count_command
from spoty.commands import print_command
from spoty.commands import export_command
from spoty.commands import import_spotify_command
from spoty.commands import import_deezer_command
from spoty.utils import SpotyContext
from spoty import settings
from spoty import log
import spoty.utils
import click


@click.group("filter")
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
@click.option('--duplicates-compare-tags', '--dct', show_default=True,
              default=settings.SPOTY.DEFAULT_COMPARE_TAGS,
              help='Compare duplicates by this tags. It is optional. You can also change the list of tags in the config file.')
@click.pass_obj
def filter_tracks(context: SpotyContext,
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

    tags_list = context.tags_list

    if len(tags_list) > 0:
        if len(leave_have_tags) > 0:
            new_tags_list = spoty.utils.filter_tags_list_have_tags(tags_list, leave_have_tags)

            if len(tags_list) - len(new_tags_list) != 0:
                context.summary.append(
                    f'{len(new_tags_list)} of {len(tags_list)} tracks left due to have all of the specified tags.')
            tags_list = new_tags_list

        if len(leave_no_tags) > 0:
            new_tags_list = spoty.utils.filter_tags_list_have_no_tags(tags_list, leave_no_tags)

            if len(tags_list) - len(new_tags_list) != 0:
                context.summary.append(
                    f'{len(new_tags_list)} of {len(tags_list)} tracks left due to not have any of the specified tags.')
            tags_list = new_tags_list

        if remove_duplicates:
            tags = duplicates_compare_tags.split(',')
            new_tags_list, dup = spoty.utils.remove_tags_duplicates(tags_list, tags, True)
            if len(dup) > 0:
                context.summary.append(f'{len(dup)} of {len(tags_list)} tracks removed due to duplicates')
            tags_list = new_tags_list

        if leave_duplicates:
            compare_tags = duplicates_compare_tags.split(',')
            new_tags_list, dup = spoty.utils.remove_tags_duplicates(tags_list, compare_tags, True)
            if len(dup) > 0:
                context.summary.append(f'{len(dup)} of {len(tags_list)} tracks left due to duplicates')
            tags_list = dup

    context.tags_list = tags_list


filter_tracks.add_command(count_command.count_tracks)
filter_tracks.add_command(print_command.print_tracks)
filter_tracks.add_command(export_command.export_tracks)
filter_tracks.add_command(import_spotify_command.import_spotify)
filter_tracks.add_command(import_deezer_command.import_deezer)
