from spoty import settings
from spoty import log
import spoty.spotify
import spoty.audio_files
import spoty.csv_playlist
import spoty.utils
from spoty.utils import SpotyContext
import click
import re
import time
import os
from datetime import datetime


@click.command("transfer")
@click.option('--dest-csv', '-C', is_flag=True,
              help='Export a list of read tracks to csv playlists on disk.')
@click.option('--dest-spotify', '-S', is_flag=True,
              help='Export a list of read tracks to playlist library.')
@click.option('--dest-option-grouping-pattern', '--dogp', show_default=True,
              default=settings.SPOTY.DEFAULT_DEST_GROUPING_PATTERN,
              help='Exported playlists/files will be named according to this pattern.')
@click.option('--dest-option-duplicates', '-d', type=bool, is_flag=True, default=False,
              help='Allow duplicates (add tracks that are already exist in the playlist).')
@click.option('--dest-option-append', '-a', is_flag=True,
              help='Add tracks to an existing playlist/file if already exists. If this option is not specified, a new playlist/file will always be created.')
@click.option('--dest-option-overwrite', '-o', is_flag=True,
              help='Overwrite existing playlist/file')
@click.option('--dest-option-path', '--dop', show_default=True,
              default=settings.SPOTY.DEFAULT_LIBRARY_PATH,
              help='The path on disk where to export csv playlists.')
@click.option('--dest-option-timestamp', '-t', is_flag=True,
              help='Create a new subfolder with the current date and time for saved csv playlists')
@click.option('--dest-option-compare-tags', '--sost', show_default=True,
              default=settings.SPOTY.DEFAULT_COMPARE_TAGS,
              help='Compare duplicates by this tags.')
@click.option('--yes-all', '-y', is_flag=True,
              help='Confirm all questions with a positive answer automatically.')
@click.pass_obj
def transfer(context:SpotyContext,

             dest_csv,
             dest_spotify,
             dest_option_grouping_pattern,
             dest_option_duplicates,
             dest_option_append,
             dest_option_overwrite,
             dest_option_path,
             dest_option_timestamp,
             dest_option_compare_tags,
             yes_all,
             ):
    """
Transfer tracks from sources to destination.
    """

    print('\n'.join(context.summary))
    print(len(context.tags_list))
    exit()



    # convert tuples to lists

    dest_option_compare_tags = dest_option_compare_tags.split(',')

    # check input parameters

    if dest_option_append and dest_option_overwrite:
        click.echo(f'Simultaneous use of "--dest-option-append" and "--dest-option-overwrite" is not possible',
                   err=True)
        exit()



    # export to destination


    import_to_csv = False
    if dest_csv:
        dest_option_path = os.path.abspath(dest_option_path)

        if dest_option_timestamp:
            now = datetime.now()
            date_time_str = now.strftime("%Y_%m_%d-%H_%M_%S")
            dest_option_path = os.path.join(dest_option_path, date_time_str)

        csv_created_file_names, csv_created_names, csv_added_tracks, csv_import_duplicates, csv_already_exist \
            = spoty.csv_playlist.create_csvs(all_tags, dest_option_path, dest_option_grouping_pattern,
                                             dest_option_overwrite, dest_option_append,
                                             dest_option_duplicates, yes_all, dest_option_compare_tags)

        import_to_csv = True

    import_to_spotify = False
    if dest_spotify:
        click.echo('Next playlists will be imported to Spotify library:')
        grouped_tags = spoty.utils.group_tags_by_pattern(all_tags, dest_option_grouping_pattern)
        for group_name, g_tags_list in grouped_tags.items():
            click.echo(group_name)
        click.echo(f'Total {len(all_tags)} tracks in {len(grouped_tags)} playlists.')

        import_to_spotify = True
        if not yes_all:
            if click.confirm(f'Do you want to continue?'):
                click.echo("")  # for new line
            else:
                click.echo("\nCanceled.")
                import_to_spotify = False
        if import_to_spotify:
            spotify_imported_playlist_ids, spotify_imported_tracks, spotify_import_duplicates, spotify_already_exist, \
            spotify_not_found = spoty.spotify.import_playlists_from_tags_list(
                all_tags, dest_option_grouping_pattern, dest_option_overwrite, dest_option_append,
                dest_option_duplicates, yes_all)

    # print summery

    if import_to_csv:
        mess = f'{len(csv_added_tracks)} tracks written to {len(csv_created_file_names)} csv playlists.'
        if len(csv_import_duplicates) > 0:
            mess += f' {len(csv_import_duplicates)} duplicates in sources skipped.'
        if len(csv_already_exist) > 0:
            mess += f' {len(csv_already_exist)} tracks already exist in csv playlists and skipped.'
        mess += f' Path: "{dest_option_path}"'
        click.echo(mess)

    if import_to_spotify:
        mess = f'{len(spotify_imported_tracks)} tracks imported in {len(spotify_imported_playlist_ids)} Spotify playlists.'
        if len(spotify_import_duplicates) > 0:
            mess += f' {len(spotify_import_duplicates)} duplicates in sources skipped.'
        if len(spotify_already_exist) > 0:
            mess += f' {len(spotify_already_exist)} tracks already exist in playlists and skipped.'
        if len(spotify_not_found) > 0:
            mess += f' {len(spotify_not_found)} tracks not found by tags.'
        click.echo(mess)


def to_list(some_tuple):
    l = []
    l.extend(some_tuple)
    return l
