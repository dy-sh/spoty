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


@click.command("move")
@click.option('--grouping-pattern', '--gp', show_default=True,
              default=settings.SPOTY.DEFAULT_GROUPING_PATTERN,
              help='Tracks will be grouped to playlists according to this pattern (for listing only).')
@click.option('--print-pattern', '--pp', show_default=True,
              default=settings.SPOTY.DEFAULT_PRINT_PATTERN,
              help='Print a list of tracks according to this formatting pattern.')
@click.option('--confirm', '-y', is_flag=True,
              help='Do not ask for confirmation')
@click.option('--path', '--p',
              help='Path where to move audio files.')
@click.pass_obj
def move_tracks(context: SpotyContext,
                grouping_pattern,
                print_pattern,
                confirm,
                path
                ):
    """
Move tracks.
    """

    all_tags_list = []
    for i, tags_list in enumerate(context.tags_lists):
        all_tags_list.extend(tags_list)

    if len(all_tags_list) == 0:
        click.echo("No tracks to move.")
        exit()

    click.echo('Next tracks will be moved:')
    for i, tags_list in enumerate(context.tags_lists):
        if len(context.tags_lists) > 1:
            click.echo()
            click.echo(
                f'============================= LIST {i + 1}/{len(context.tags_lists)} =============================')
            click.echo()

        spoty.utils.print_tags_list_grouped(tags_list, print_pattern, grouping_pattern)

    if not confirm:
        click.confirm(f'Are you sure you want to move {len(all_tags_list)} tracks?', abort=True)

    context.summary.append('Moving:')

    moved_spotify_tracks, moved_deezer_tracks, moved_audio_files, moved_csv_tracks = \
        move_tracks_from_all_sources(all_tags_list, path)

    if len(moved_spotify_tracks) > 0:
        context.summary.append(f'  {len(moved_spotify_tracks)} tracks moved from Spotify.')

    if len(moved_deezer_tracks) > 0:
        context.summary.append(f'  {len(moved_deezer_tracks)} tracks moved from Deezer.')

    if len(moved_audio_files) > 0:
        context.summary.append(f'  {len(moved_audio_files)} audio files moved.')

    if len(moved_csv_tracks) > 0:
        context.summary.append(f'  {len(moved_csv_tracks)} tracks from csv moved.')

    click.echo('\n------------------------------------------------------------')
    click.echo('\n'.join(context.summary))


def move_tracks_from_all_sources(all_tags_list, path):
    spotify_playlists, deezer_playlists, local_audio_files, csv_playlists = spoty.utils.sort_tracks_by_source(
        all_tags_list)

    # todo move deezer, spotify, csv tracks

    moved_audio_files = []
    if len(local_audio_files) > 0:
        for file_name in local_audio_files:
            if spoty.utils.is_valid_file(file_name):
                shutil.move(file_name, path)
                moved_audio_files.append(file_name)

    moved_spotify_tracks = []
    moved_deezer_tracks = []
    moved_csv_tracks = []

    return moved_spotify_tracks, moved_deezer_tracks, moved_audio_files, moved_csv_tracks
