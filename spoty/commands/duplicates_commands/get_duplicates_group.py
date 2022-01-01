from spoty.commands.first_list_commands import \
    count_command, \
    delete_command, \
    copy_command, \
    move_command, \
    export_command, \
    import_deezer_command, \
    import_spotify_command, \
    find_deezer_group2, \
    find_spotify_group2, \
    print_command, \
    create_m3u8_command
from spoty.utils import SpotyContext
import click


@click.group("get")
@click.option('--only-def', '--od', '-d', is_flag=True,
              help='Get only definitely duplicates.')
@click.option('--only-prob', '--op', '-p', is_flag=True,
              help='Get only probably duplicates.')
@click.pass_obj
def get_duplicates(context: SpotyContext,
                   only_def,
                   only_prob
                   ):
    """
Get duplicates for further actions (see next commands).
    """

    if only_def and only_prob:
        click.echo(f'Simultaneous use of "--only-def" and "--only-prob" is not possible', err=True)
        exit()

    context.tags_lists.clear()
    context.tags_lists.append([])

    for group in context.duplicates_groups:
        if not only_prob:
            context.tags_lists[0].extend(group.def_duplicates)
        if not only_def:
            context.tags_lists[0].extend(group.prob_duplicates)

    context.summary.append("Collecting duplicates:")
    context.summary.append(f'  {len(context.tags_lists[0])} duplicates collected.')

    context.duplicates_groups = []
    context.unique_first_tracks = []
    context.unique_second_tracks = []

get_duplicates.add_command(count_command.count_tracks)
get_duplicates.add_command(print_command.print_tracks)
get_duplicates.add_command(export_command.export_tracks)
get_duplicates.add_command(create_m3u8_command.export_tracks)
get_duplicates.add_command(import_spotify_command.import_spotify)
get_duplicates.add_command(import_deezer_command.import_deezer)
get_duplicates.add_command(find_deezer_group2.find_deezer)
get_duplicates.add_command(find_spotify_group2.find_spotify)
get_duplicates.add_command(delete_command.delete_tracks)
get_duplicates.add_command(move_command.move_tracks)
get_duplicates.add_command(copy_command.copy_tracks)

