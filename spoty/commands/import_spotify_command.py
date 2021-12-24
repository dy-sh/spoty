from spoty import settings
from spoty import log
import spoty.spotify_api
import spoty.csv_playlist
import spoty.utils
from spoty.utils import SpotyContext
import click
import os
from datetime import datetime

@click.command("import-spotify")
@click.option('--grouping-pattern', '--gp', show_default=True,
              default=settings.SPOTY.DEFAULT_GROUPING_PATTERN,
              help='Tracks will be grouped to playlists according to this pattern.')
@click.option('--duplicates', '-d', type=bool, is_flag=True, default=False,
              help='Allow duplicates (add tracks that are already exist in the playlist).')
@click.option('--append', '-a', is_flag=True,
              help='Add tracks to an existing playlist if already exists. If this option is not specified, a new playlist will always be created.')
@click.option('--overwrite', '-o', is_flag=True,
              help='Overwrite existing playlist')
# @click.option('--duplicates-compare-tags', '--dct', show_default=True,
#               default=settings.SPOTY.DEFAULT_COMPARE_TAGS,
#               help='Compare duplicates by this tags. It is optional. You can also change the list of tags in the config file.')
@click.option('--yes-all', '-y', is_flag=True,
              help='Confirm all questions with a positive answer automatically.')
@click.option('--export-result', '-r', is_flag=True,
              help='Export csv files with result (imported, not found, skipped tracks)')
@click.option('--result-path', '--rp',
              default=settings.SPOTY.DEFAULT_EXPORT_PATH,
              help='Path to create resulting csv files')
@click.pass_obj
def import_spotify(context: SpotyContext,
                   grouping_pattern,
                   duplicates,
                   append,
                   overwrite,
                   # duplicates_compare_tags,
                   yes_all,
                   export_result,
                   result_path
                   ):
    """
Import track list to Spotify Library
    """

    for tags_list in context.tags_lists:

        if append and overwrite:
            click.echo(f'Simultaneous use of "--append" and "--overwrite" is not possible',
                       err=True)
            exit()

        click.echo('Next playlists will be imported to Spotify library:')
        grouped_tags = spoty.utils.group_tags_by_pattern(tags_list, grouping_pattern)
        for group_name, g_tags_list in grouped_tags.items():
            click.echo("  " + group_name)
        click.echo(f'Total {len(tags_list)} tracks in {len(grouped_tags)} playlists.')

        if not yes_all:
            if click.confirm(f'Do you want to continue?'):
                click.echo("")  # for new line
            else:
                click.echo("\nCanceled.")
                exit()

        found_tags_list, not_found_tags_list = spoty.spotify_api.find_missing_track_ids(tags_list)

        playlist_ids, imported_tags_list, source_duplicates_tags_list, already_exist_tags_list = \
            spoty.spotify_api.import_playlists_from_tags_list(
                found_tags_list, grouping_pattern, overwrite, append, duplicates, yes_all)

        # create result csv playlists

        if export_result:
            result_path = os.path.abspath(result_path)
            date_time_str = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
            result_path = os.path.join(result_path, 'import-spotify-' + date_time_str)

            if len(imported_tags_list) > 0:
                path = os.path.join(result_path, 'imported')
                spoty.csv_playlist.create_csvs(imported_tags_list, path, grouping_pattern)
            if len(source_duplicates_tags_list) > 0:
                path = os.path.join(result_path, 'skipped_source_duplicates')
                spoty.csv_playlist.create_csvs(source_duplicates_tags_list, path, grouping_pattern)
            if len(already_exist_tags_list) > 0:
                path = os.path.join(result_path, 'skipped_already_exist')
                spoty.csv_playlist.create_csvs(already_exist_tags_list, path, grouping_pattern)
            if len(not_found_tags_list) > 0:
                path = os.path.join(result_path, 'not_found')
                spoty.csv_playlist.create_csvs(not_found_tags_list, path, grouping_pattern)

        # print summery

        context.summary.append("Importing to Spotify:")
        if len(source_duplicates_tags_list) > 0:
            context.summary.append(f'  {len(source_duplicates_tags_list)} duplicates in collected tracks skipped.')
        if len(already_exist_tags_list) > 0:
            context.summary.append(f'  {len(already_exist_tags_list)} tracks already exist in playlists and skipped.')
        if len(not_found_tags_list) > 0:
            context.summary.append(f'  {len(not_found_tags_list)} tracks not found by tags.')

        if len(imported_tags_list) == 0:
            context.summary.append(f'  No tracks to import.')
        else:
            if len(playlist_ids) == 1:
                context.summary.append(f'  {len(imported_tags_list)} tracks imported in Spotify playlist.')
            else:
                context.summary.append(f'  {len(imported_tags_list)} tracks imported in {len(playlist_ids)} Spotify playlists.')

    click.echo('\n------------------------------------------------------------')
    click.echo('\n'.join(context.summary))
