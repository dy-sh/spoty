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
    find_duplicates_command,\
    create_m3u8_command
from spoty.commands import get_second_group
from spoty import settings
from spoty import log
import spoty.spotify_api
import spoty.csv_playlist
import spoty.utils
from spoty.utils import SpotyContext
import click
import os
from datetime import datetime


@click.group("find-spotify")
@click.option('--grouping-pattern', '--gp', show_default=True,
              default=settings.SPOTY.DEFAULT_GROUPING_PATTERN,
              help='Tracks will be grouped to playlists according to this pattern (only for exporting csv result files).')
@click.option('--ignore-duration', '-i', is_flag=True,
              help='Dont match track duration')
@click.option('--export-result', '-r', is_flag=True,
              help='Export csv files with result (imported, not found, skipped tracks)')
@click.option('--result-path', '--rp',
              default=settings.SPOTY.DEFAULT_EXPORT_PATH,
              help='Path to create resulting csv files')
@click.pass_obj
def find_spotify(context: SpotyContext,
                 grouping_pattern,
                 ignore_duration,
                 export_result,
                 result_path
                 ):
    """
Find tracks in Spotify.
    """

    tags_list = context.tags_lists[0]
    tags_with_ids = []
    tags_without_ids = []
    for tags in tags_list:
        if 'SPOTIFY_TRACK_ID' in tags:
            tags_with_ids.append(tags)
        else:
            tags_without_ids.append(tags)

    found_tags_list, not_found_tags_list = spoty.spotify_api.find_missing_track_ids(tags_list, ignore_duration)

    context.tags_lists[0] = found_tags_list

    # create result csv playlists

    if export_result:
        result_path = os.path.abspath(result_path)
        date_time_str = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
        result_path = os.path.join(result_path, 'import-spotify-' + date_time_str)

        if len(found_tags_list) > 0:
            path = os.path.join(result_path, 'found')
            spoty.csv_playlist.create_csvs(found_tags_list, path, grouping_pattern)
        if len(not_found_tags_list) > 0:
            path = os.path.join(result_path, 'not_found')
            spoty.csv_playlist.create_csvs(not_found_tags_list, path, grouping_pattern)

    # print summery

    context.summary.append("Finding in Spotify:")
    if len(tags_with_ids) > 0:
        context.summary.append(f'  {len(tags_with_ids)} tracks have SPOTIFY_TRACK_ID tag and skipped.')
    if len(found_tags_list) > 0:
        context.summary.append(f'  {len(found_tags_list)} tracks found.')
    if len(not_found_tags_list) > 0:
        context.summary.append(f'  {len(not_found_tags_list)} tracks not found.')


find_spotify.add_command(count_command.count_tracks)
find_spotify.add_command(print_command.print_tracks)
find_spotify.add_command(export_command.export_tracks)
find_spotify.add_command(create_m3u8_command.export_tracks)
find_spotify.add_command(import_spotify_command.import_spotify)
find_spotify.add_command(import_deezer_command.import_deezer)
find_spotify.add_command(sync_spotify_command.sync_spotify)
# find_spotify.add_command(get_second_group.get_second)
find_spotify.add_command(delete_command.delete_tracks)
find_spotify.add_command(move_command.move_tracks)
find_spotify.add_command(copy_command.copy_tracks)
# find_spotify.add_command(find_duplicates_command.find_duplicates)