from spoty import settings
from spoty import log
from spoty.utils import SpotyContext
from spoty.commands.first_list_commands import delete_command
import spoty.utils
import click
import os

@click.command("move")
@click.option('--path', '--p', show_default=True,
              default=settings.SPOTY.DEFAULT_EXPORT_PATH,
              help='The path on disk where to move duplicated audio files.')
@click.option('--print-pattern', '--pp', show_default=True,
              help='Print a list of tracks according to this formatting pattern. If not specified, R setting from the config file will be used.')
@click.option('--confirm', '-y', type=bool, is_flag=True, default=False,
              help='Do not ask for confirmation')
@click.pass_obj
def move_duplicates(context: SpotyContext,
                    path,
                    print_pattern,
                    confirm
                    ):
    """
Move duplicated audio files to specified path.
    """
    # export result to  csv files
    path = os.path.abspath(path)

    all_tags_list = []
    for group in context.duplicates_groups:
        all_tags_list.extend(group.def_duplicates)
        all_tags_list.extend(group.prob_duplicates)

    if len(all_tags_list) == 0:
        click.echo("No audio files to move.")
        exit()

    click.echo(f'Next audio files will be moved to "{path}":')

    for i, group in enumerate(context.duplicates_groups):
        if len(group.def_duplicates) > 0:
            spoty.utils.print_duplicates_tags_list(group.def_duplicates, print_pattern)
        if len(group.prob_duplicates) > 0:
            spoty.utils.print_duplicates_tags_list(group.prob_duplicates, print_pattern)

    if not confirm:
        click.confirm(f'Are you sure you want to move {len(all_tags_list)} audio files?', abort=True)

    context.summary.append('Moving:')

    moved_files = spoty.utils.move_audio_files_to_path(all_tags_list,path)

    if len(moved_files) > 0:
        context.summary.append(f'  {len(moved_files)} audio files moved.')


    click.echo('\n------------------------------------------------------------')
    click.echo('\n'.join(context.summary))


