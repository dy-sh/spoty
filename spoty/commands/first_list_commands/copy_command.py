from spoty import settings
from spoty import log
from spoty.utils import SpotyContext
import spoty.utils
import spoty.spotify_api
import spoty.deezer_api
import spoty.audio_files
import click
import shutil
import os


@click.command("copy")
@click.option('--grouping-pattern', '--gp', show_default=True,
              default=settings.SPOTY.DEFAULT_GROUPING_PATTERN,
              help='Tracks will be grouped to playlists according to this pattern (for listing only).')
@click.option('--print-pattern', '--pp', show_default=True,
              default=settings.SPOTY.DEFAULT_PRINT_PATTERN,
              help='Print a list of tracks according to this formatting pattern.')
@click.option('--confirm', '-y', is_flag=True,
              help='Do not ask for confirmation')
@click.option('--path', '--p',
              help='Path where to copy audio files.')
@click.pass_obj
def copy_tracks(context: SpotyContext,
                grouping_pattern,
                print_pattern,
                confirm,
                path
                ):
    """
Copy tracks.
    """

    all_tags_list = []
    for i, tags_list in enumerate(context.tags_lists):
        all_tags_list.extend(tags_list)

    if len(all_tags_list) == 0:
        context.summary.append("No tracks to copy.")
    else:
        click.echo('Next tracks will be copied:')
        for i, tags_list in enumerate(context.tags_lists):
            if len(context.tags_lists) > 1:
                click.echo()
                click.echo(
                    f'============================= LIST {i + 1}/{len(context.tags_lists)} =============================')
                click.echo()

            spoty.utils.print_tags_list_grouped(tags_list, print_pattern, grouping_pattern)

        if not confirm:
            click.confirm(f'Are you sure you want to copy {len(all_tags_list)} tracks?', abort=True)

        context.summary.append('Copying:')

        copied_spotify_tracks, copied_deezer_tracks, copied_audio_files, copied_csv_tracks = \
            copy_tracks_from_all_sources(all_tags_list, path)

        if len(copied_spotify_tracks) > 0:
            context.summary.append(f'  {len(copied_spotify_tracks)} tracks copied from Spotify.')

        if len(copied_deezer_tracks) > 0:
            context.summary.append(f'  {len(copied_deezer_tracks)} tracks copied from Deezer.')

        if len(copied_audio_files) > 0:
            context.summary.append(f'  {len(copied_audio_files)} audio files copied.')

        if len(copied_csv_tracks) > 0:
            context.summary.append(f'  {len(copied_csv_tracks)} tracks from csv copied.')

    click.echo('\n------------------------------------------------------------')
    click.echo('\n'.join(context.summary))


def copy_tracks_from_all_sources(all_tags_list, path):
    spotify_playlists, deezer_playlists, local_audio_files, csv_playlists = spoty.utils.sort_tracks_by_source(
        all_tags_list)

    # todo move deezer, spotify, csv tracks

    copied_audio_files = []
    if len(local_audio_files) > 0:
        if path is None:
            click.echo("Cant copy local files. Option --path is not specified. Skipped.")
        else:
            with click.progressbar(local_audio_files, label=f'Copying {len(local_audio_files)} files') as bar:
                for file_name in bar:
                    if spoty.utils.is_valid_file(file_name):
                        base_name = os.path.basename(file_name)
                        new_file_name = os.path.join(path, base_name)
                        if os.path.isfile(new_file_name):
                            new_file_name = spoty.utils.find_empty_file_name(new_file_name)
                        shutil.copy(file_name, new_file_name)

    copied_spotify_tracks = []
    copied_deezer_tracks = []
    copied_csv_tracks = []

    return copied_spotify_tracks, copied_deezer_tracks, copied_audio_files, copied_csv_tracks
