from spoty import settings
from spoty import log
from spoty.utils import SpotyContext
import spoty.utils
import spoty.spotify_api
import spoty.deezer_api
import spoty.audio_files
import click
import os


@click.command("delete")
@click.option('--grouping-pattern', '--gp', show_default=True,
              default=settings.SPOTY.DEFAULT_GROUPING_PATTERN,
              help='Tracks will be grouped to playlists according to this pattern (for listing only).')
@click.option('--print-pattern', '--pp', show_default=True,
              default=settings.SPOTY.DEFAULT_PRINT_PATTERN,
              help='Print a list of tracks according to this formatting pattern.')
# @click.option('--export-result', '-r', is_flag=True,
#               help='Export csv files with result (list of deleted tracks)')
# @click.option('--result-path', '--rp',
#               default=settings.SPOTY.DEFAULT_EXPORT_PATH,
#               help='Path to create resulting csv files')
@click.option('--confirm', '-y', is_flag=True,
              help='Do not ask for confirmation')
@click.pass_obj
def delete_tracks(context: SpotyContext,
                  grouping_pattern,
                  print_pattern,
                  # export_result,
                  # result_path,
                  confirm
                  ):
    """
Delete tracks.
    """
    context.summary.append('Deleting:')

    all_tags_list = []
    for i, tags_list in enumerate(context.tags_lists):
        all_tags_list.extend(tags_list)

    if len(all_tags_list) == 0:
        context.summary.append("  No tracks to delete.")
    else:
        click.echo('Next tracks will be deleted:')
        for i, tags_list in enumerate(context.tags_lists):
            if len(context.tags_lists) > 1:
                click.echo()
                click.echo(
                    f'============================= LIST {i + 1}/{len(context.tags_lists)} =============================')
                click.echo()

            spoty.utils.print_tags_list_grouped(tags_list, print_pattern, grouping_pattern)

        if not confirm:
            click.confirm(f'Are you sure you want to delete {len(all_tags_list)} tracks?', abort=True)



        deleted_spotify_tracks, deleted_deezer_tracks, deleted_audio_files, deleted_csv_tracks = \
            delete_tracks_from_all_sources(all_tags_list)

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


def delete_tracks_from_all_sources(all_tags_list):
    spotify_playlists, deezer_playlists, local_audio_files, csv_playlists = spoty.utils.sort_tracks_by_source(all_tags_list)

    # todo: delete from csv

    deleted_spotify_tracks = []
    if len(spotify_playlists.keys()) > 0:
        for playlist_id, track_ids in spotify_playlists.items():
            spoty.spotify_api.remove_tracks_from_playlist(playlist_id, track_ids)
            deleted_spotify_tracks.extend(track_ids)

    deleted_deezer_tracks = []
    if len(deezer_playlists.keys()) > 0:
        for playlist_id, track_ids in deezer_playlists.items():
            spoty.deezer_api.remove_tracks_from_playlist(playlist_id, track_ids)
            deleted_deezer_tracks.extend(track_ids)

    deleted_audio_files = []
    if len(local_audio_files) > 0:
        for file_name in local_audio_files:
            if spoty.utils.is_valid_file(file_name):
                os.remove(file_name)
                deleted_audio_files.append(file_name)

    deleted_csv_tracks = []

    return deleted_spotify_tracks, deleted_deezer_tracks, deleted_audio_files, deleted_csv_tracks
