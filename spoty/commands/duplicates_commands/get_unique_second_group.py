from spoty.commands.first_list_commands import \
    count_command, \
    delete_command, \
    copy_command, \
    move_command, \
    export_command, \
    import_deezer_command, \
    import_spotify_command, \
    sync_spotify_command, \
    print_command, \
    create_m3u8_command
from spoty.utils import SpotyContext
import click


@click.group("get-unique")
@click.option('--fist-list', '--fl', '-f', is_flag=True,
              help='Get unique tracks only from first collected list.')
@click.option('--second-list', '--sl', '-s', is_flag=True,
              help='Get unique tracks only from second collected list.')
@click.pass_obj
def get_unique(context: SpotyContext,
               fist_list,
               second_list
               ):
    """
Get unique tracks (not duplicated) for further actions (see next commands).
    """

    if not fist_list and not second_list:
        click.echo(f'Please, specify --fist-list or --second-list (or both) for "get-unique" command.', err=True)
        exit()

    context.summary.append("Collecting unique tracks:")

    context.tags_lists.clear()
    context.tags_lists.append([])

    if fist_list:
        context.tags_lists[0].extend(context.unique_first_tracks)
        context.summary.append(f'  {len(context.unique_first_tracks)} unique tracks from first list collected.')
    if second_list:
        context.tags_lists[0].extend(context.unique_second_tracks)
        context.summary.append(f'  {len(context.unique_second_tracks)} unique tracks from second list collected.')

    if len(context.tags_lists[0]) == 0:
        context.summary.append(f'  0 unique tracks collected.')

    context.duplicates_groups = []
    context.unique_first_tracks = []
    context.unique_second_tracks = []

get_unique.add_command(count_command.count_tracks)
get_unique.add_command(print_command.print_tracks)
get_unique.add_command(export_command.export_tracks)
get_unique.add_command(create_m3u8_command.export_tracks)
get_unique.add_command(import_spotify_command.import_spotify)
get_unique.add_command(import_deezer_command.import_deezer)
get_unique.add_command(sync_spotify_command.sync_spotify)
get_unique.add_command(delete_command.delete_tracks)
get_unique.add_command(move_command.move_tracks)
get_unique.add_command(copy_command.copy_tracks)
