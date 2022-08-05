from spoty import settings
from spoty import log
import spoty.csv_playlist
import spoty.utils
from spoty.utils import SpotyContext
import click
import os
from datetime import datetime


@click.command("export")
@click.option('--grouping-pattern', '--gp', show_default=True,
              default=settings.SPOTY.DEFAULT_EXPORT_GROUPING_PATTERN,
              help='Tracks will be grouped to playlists according to this pattern.')
@click.option('--no-duplicates', '-D', is_flag=True,
              help='Prevent duplicates (remove tracks that are already exist in csv file).')
@click.option('--append', '-a', is_flag=True,
              help='Add tracks to an existing csv file if already exists. If this option is not specified, a new csv file will always be created.')
@click.option('--overwrite', '-o', is_flag=True,
              help='Overwrite existing csv file')
@click.option('--path', '--p', show_default=True,
              default=settings.SPOTY.DEFAULT_EXPORT_PATH,
              help='The path on disk where to export csv files.')
@click.option('--no-timestamp', '-T', is_flag=True,
              help='Do not create a subfolder with the current date and time for saved csv files.')
@click.option('--duplicates-compare-tags', '--dct', show_default=True, multiple=True,
              default=settings.SPOTY.COMPARE_TAGS_DEFINITELY_DUPLICATE,
              help='Compare duplicates by this tags. It is optional. You can also change the list of tags in the config file.')
@click.option('--get-only-tags', '--got',
              help='Get only specified tags. All other tags will be removed. or Example: "SPOTIFY_TRACK_ID,ISRC,ARTIST,TITLE"')
@click.option('--confirm', '-y', is_flag=True,
              help='Confirm all questions with a positive answer automatically.')
@click.pass_obj
def export_tracks(context: SpotyContext,
                  grouping_pattern,
                  no_duplicates,
                  append,
                  overwrite,
                  path,
                  no_timestamp,
                  duplicates_compare_tags,
                  get_only_tags,
                  confirm,
                  ):
    """
Export a list of tracks to csv files (playlists) on disk.
    """

    for tags_list in context.tags_lists:

        if append and overwrite:
            click.echo(f'Simultaneous use of "--append" and "--overwrite" is not possible',
                       err=True)
            exit()

        path = os.path.abspath(path)

        if not no_timestamp:
            now = datetime.now()
            date_time_str = now.strftime("%Y_%m_%d-%H_%M_%S")
            path = os.path.join(path, "export-csv-" + date_time_str)

        if get_only_tags:
            get_only_tags = str.split(get_only_tags, ',')

        file_names, names, added_tracks, import_duplicates, already_exist \
            = spoty.csv_playlist.create_csvs(tags_list, path, grouping_pattern, overwrite, append, no_duplicates,
                                             confirm, duplicates_compare_tags, get_only_tags)

        # print summery

        context.summary.append("Exporting:")
        if len(import_duplicates) > 0:
            context.summary.append(f'  {len(import_duplicates)} duplicates in collected tracks skipped.')
        if len(already_exist) > 0:
            context.summary.append(f'  {len(already_exist)} tracks already exist in csv files and skipped.')

        if len(added_tracks) == 0:
            context.summary.append(f'  No tracks to export.')
        else:
            if len(file_names) == 1:
                context.summary.append(f'  {len(added_tracks)} tracks written to csv file (path: "{path}").')
            else:
                context.summary.append(
                    f'  {len(added_tracks)} tracks written to {len(file_names)} csv files (path: "{path}").')

    click.echo('\n------------------------------------------------------------')
    click.echo('\n'.join(context.summary))
