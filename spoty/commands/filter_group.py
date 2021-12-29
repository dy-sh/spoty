from spoty.commands.first_list_commands import \
    count_command, \
    delete_command, \
    export_command, \
    import_deezer_command, \
    import_spotify_command, \
    print_command, \
    find_duplicates_command,\
    create_m3u8_command
from spoty.commands import get_second_group
from spoty.utils import SpotyContext
from spoty import settings
import spoty.utils
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
@click.option('--leave-added-after', '--lab',
              help='Leave only added to playlist after specified date.')
@click.pass_obj
def filter_tracks(context: SpotyContext,
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

    filter_tracks_wrapper(context,
                          # playlist_names,
                          leave_have_tags,
                          leave_no_tags,
                          remove_duplicates,
                          leave_duplicates,
                          duplicates_compare_tags,
                          leave_added_before,
                          leave_added_after,
                          )


def filter_tracks_wrapper(context: SpotyContext,
                          # playlist_names,
                          leave_have_tags,
                          leave_no_tags,
                          remove_duplicates,
                          leave_duplicates,
                          duplicates_compare_tags,
                          leave_added_before,
                          leave_added_after,
                          ):
    tags_list = context.tags_lists[-1]  # get last tags list

    if len(tags_list) > 0:
        summary = []
        summary.append("Filtering:")

        if len(leave_have_tags) > 0:
            new_tags_list = spoty.utils.filter_tags_list_have_tags(tags_list, leave_have_tags)
            if len(tags_list) - len(new_tags_list) != 0:
                summary.append(
                    f'  {len(tags_list) - len(new_tags_list)}/{len(tags_list)} tracks removed (have all of the specified tags).')
            tags_list = new_tags_list

        if len(leave_no_tags) > 0:
            new_tags_list = spoty.utils.filter_tags_list_have_no_tags(tags_list, leave_no_tags)
            if len(tags_list) - len(new_tags_list) != 0:
                summary.append(
                    f'  {len(tags_list) - len(new_tags_list)}/{len(tags_list)} tracks removed (not have any of the specified tags).')
            tags_list = new_tags_list

        if remove_duplicates:
            compare_tags_list = spoty.utils.tuple_to_list(duplicates_compare_tags)
            for compare_tags_str in compare_tags_list:
                compare_tags = compare_tags_str.split(',')
                new_tags_list, dup = spoty.utils.remove_duplicated_tags(tags_list, compare_tags, False)
                if len(dup) > 0:
                    summary.append(
                        f'  {len(dup)}/{len(tags_list)} tracks removed (duplicates by tags: {compare_tags_str})')
                tags_list = new_tags_list

        if leave_duplicates:
            compare_tags_list = spoty.utils.tuple_to_list(duplicates_compare_tags)
            all_dup = []
            for compare_tags_str in compare_tags_list:
                compare_tags = compare_tags_str.split(',')
                new_tags_list, dup = spoty.utils.remove_duplicated_tags(tags_list, compare_tags, False)
                if len(dup) > 0:
                    summary.append(
                        f'   {len(dup)}/{len(tags_list)} tracks left (duplicates by tags: {compare_tags_str})')
                tags_list = new_tags_list
                all_dup.extend(dup)
            tags_list = all_dup

        if leave_added_after:
            new_tags_list = spoty.utils.filter_added_after_date(tags_list, leave_added_after)
            if len(tags_list) - len(new_tags_list) != 0:
                summary.append(
                    f'  {len(tags_list) - len(new_tags_list)}/{len(tags_list)} tracks removed (not added after specified date).')
            tags_list = new_tags_list

        if leave_added_before:
            new_tags_list = spoty.utils.filter_added_before_date(tags_list, leave_added_before)
            if len(tags_list) - len(new_tags_list) != 0:
                summary.append(
                    f'  {len(tags_list) - len(new_tags_list)}/{len(tags_list)} tracks removed (not added before specified date).')
            tags_list = new_tags_list


        if len(summary) > 1:
            context.summary.extend(summary)

    context.tags_lists[-1] = tags_list


filter_tracks.add_command(count_command.count_tracks)
filter_tracks.add_command(print_command.print_tracks)
filter_tracks.add_command(export_command.export_tracks)
filter_tracks.add_command(create_m3u8_command.export_tracks)
filter_tracks.add_command(import_spotify_command.import_spotify)
filter_tracks.add_command(import_deezer_command.import_deezer)
filter_tracks.add_command(get_second_group.get_second)
filter_tracks.add_command(delete_command.delete_tracks)
filter_tracks.add_command(find_duplicates_command.find_duplicates)
