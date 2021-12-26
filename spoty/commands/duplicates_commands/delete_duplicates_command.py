from spoty import settings
from spoty import log
from spoty.utils import SpotyContext
from spoty.commands.first_list_commands import delete_command
import spoty.utils
import click


@click.command("delete")
@click.option('--print-pattern', '--pp', show_default=True,
              help='Print a list of tracks according to this formatting pattern. If not specified, DUPLICATE_PRINT_PATTERN setting from the config file will be used.')
@click.option('--confirm', '-y', type=bool, is_flag=True, default=False,
              help='Do not ask for confirmation')
@click.pass_obj
def delete_duplicates(context: SpotyContext,
                      print_pattern,
                      confirm
                     ):
    """
Delete duplicates in destination path.
    """

    all_tags_list = []
    for group in context.duplicates_groups:
        all_tags_list.extend(group.dest_def_duplicates)
        all_tags_list.extend(group.dest_prob_duplicates)

    if len(all_tags_list) == 0:
        click.echo("No tracks to delete.")
        exit()

    click.echo('Next tracks will be deleted:')

    for i, group in enumerate(context.duplicates_groups):
        if len(group.dest_def_duplicates) > 0:
            spoty.utils.print_duplicates_tags_list(group.dest_def_duplicates, print_pattern)
        if len(group.dest_prob_duplicates) > 0:
            spoty.utils.print_duplicates_tags_list(group.dest_prob_duplicates, print_pattern)

    if not confirm:
        click.confirm(f'Are you sure you want to delete {len(all_tags_list)} tracks?', abort=True)

    context.summary.append('Deleting:')

    deleted_spotify_tracks, deleted_deezer_tracks, deleted_audio_files, deleted_csv_tracks = \
        delete_command.delete_tracks_from_all_sources(all_tags_list)

    if len(deleted_spotify_tracks) > 0:
        context.summary.append(f'  {len(deleted_spotify_tracks)} tracks deleted from Spotify.')

    if len(deleted_deezer_tracks) > 0:
        context.summary.append(f'  {len(deleted_deezer_tracks)} tracks deleted from Deezer.')

    if len(deleted_audio_files) > 0:
        context.summary.append(f'  {len(deleted_audio_files)} audio files deleted.')

    if len(deleted_csv_tracks) > 0:
        context.summary.append(f'  {len(deleted_csv_tracks)} tracks from csv deleted.')

    click.echo('\n------------------------------------------------------------')
    click.echo('\n'.join(context.summary))
