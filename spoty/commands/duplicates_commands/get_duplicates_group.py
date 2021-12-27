from spoty.commands.first_list_commands import \
    count_command, \
    delete_command, \
    export_command, \
    import_deezer_command, \
    import_spotify_command, \
    print_command
from spoty.commands import \
    filter_group
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

    all_tags_list = []
    for group in context.duplicates_groups:
        if not only_prob:
            all_tags_list.extend(group.def_duplicates)
        if not only_def:
            all_tags_list.extend(group.prob_duplicates)

    context.tags_lists.clear()
    context.tags_lists.append(all_tags_list)

    context.summary.append("Collecting:")
    context.summary.append(f'  {len(all_tags_list)} duplicates collected.')


get_duplicates.add_command(count_command.count_tracks)
get_duplicates.add_command(print_command.print_tracks)
get_duplicates.add_command(export_command.export_tracks)
get_duplicates.add_command(import_spotify_command.import_spotify)
get_duplicates.add_command(import_deezer_command.import_deezer)
get_duplicates.add_command(delete_command.delete_tracks)

