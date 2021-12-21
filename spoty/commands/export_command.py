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


@click.command("export")
@click.option('--grouping-pattern', '--gp', show_default=True,
              default=settings.SPOTY.DEFAULT_DEST_GROUPING_PATTERN,
              help='Tracks will be grouped to playlists according to this pattern.')
@click.option('--duplicates', '-d', type=bool, is_flag=True, default=False,
              help='Allow duplicates (add tracks that are already exist in the playlist).')
@click.option('--append', '-a', is_flag=True,
              help='Add tracks to an existing csv file if already exists. If this option is not specified, a new csv file will always be created.')
@click.option('--overwrite', '-o', is_flag=True,
              help='Overwrite existing csv file')
@click.option('--path', '--p', show_default=True,
              default=settings.SPOTY.DEFAULT_LIBRARY_PATH,
              help='The path on disk where to export csv files.')
@click.option('--timestamp', '-t', is_flag=True,
              help='Create a new subfolder with the current date and time for saved csv files')
@click.option('--duplicates-compare-tags', '--dct', show_default=True,
              default=settings.SPOTY.DEFAULT_COMPARE_TAGS,
              help='Compare duplicates by this tags. It is optional. You can also change the list of tags in the config file.')
@click.option('--yes-all', '-y', is_flag=True,
              help='Confirm all questions with a positive answer automatically.')
@click.pass_obj
def export_tracks(context: SpotyContext,

                  grouping_pattern,
                  duplicates,
                  append,
                  overwrite,
                  path,
                  timestamp,
                  duplicates_compare_tags,
                  yes_all,
                  ):
    """
Export a list of tracks to csv files (playlists) on disk.
    """

    tags_list = context.tags_list

    if append and overwrite:
        click.echo(f'Simultaneous use of "--append" and "--overwrite" is not possible',
                   err=True)
        exit()

    path = os.path.abspath(path)

    if timestamp:
        now = datetime.now()
        date_time_str = now.strftime("%Y_%m_%d-%H_%M_%S")
        path = os.path.join(path, date_time_str)

    compare_tags = duplicates_compare_tags.split(',')

    file_names, names, added_tracks, import_duplicates, already_exist \
        = spoty.csv_playlist.create_csvs(tags_list, path, grouping_pattern, overwrite, append, duplicates, yes_all,
                                         compare_tags)

    import_to_csv = True

    # print summery

    context.summary.append( f'{len(added_tracks)} tracks written to {len(file_names)} csv files.')
    if len(import_duplicates) > 0:
        context.summary.append( f'{len(import_duplicates)} duplicates in collected tracks skipped.')
    if len(already_exist) > 0:
        context.summary.append( f'{len(already_exist)} tracks already exist in csv files and skipped.')
    context.summary.append( f'Export path: "{path}"')

    click.echo('\n------------------------------------------------------------')
    click.echo('\n'.join(context.summary))