from spoty import settings
from spoty import log
import spoty.m3u8_playlist
import spoty.utils
from spoty.utils import SpotyContext
import click
import os
from datetime import datetime


@click.command("create-m3u8")
@click.option('--grouping-pattern', '--gp', show_default=True,
              default=settings.SPOTY.DEFAULT_GROUPING_PATTERN,
              help='Tracks will be grouped to playlists according to this pattern.')
@click.option('--no-duplicates', '-D', is_flag=True,
              help='Prevent duplicates (remove tracks that are already exist in m3u8 file).')
@click.option('--append', '-a', is_flag=True,
              help='Add tracks to an existing m3u8 file if already exists. If this option is not specified, a new m3u8 file will always be created.')
@click.option('--overwrite', '-o', is_flag=True,
              help='Overwrite existing m3u8 file')
@click.option('--path', '--p', show_default=True,
              default=settings.SPOTY.DEFAULT_EXPORT_PATH,
              help='The path on disk where to export m3u8 files.')
@click.option('--no-timestamp', '-T', is_flag=True,
              help='Do not create a subfolder with the current date and time for saved m3u8 files')
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
                  confirm,
                  ):
    """
Export a list of audio files to m3u8 files playlists.
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
            path = os.path.join(path, "export-m3u8-" + date_time_str)

        file_names, names, added_tracks, import_duplicates, already_exist \
            = spoty.m3u8_playlist.create_m3u8s(tags_list, path, grouping_pattern, overwrite, append, no_duplicates,
                                               confirm,
                                               ["SPOTY_FILE_NAME"])

        # print summery

        context.summary.append("Exporting:")
        if len(import_duplicates) > 0:
            context.summary.append(f'  {len(import_duplicates)} duplicates in collected tracks skipped.')
        if len(already_exist) > 0:
            context.summary.append(f'  {len(already_exist)} tracks already exist in m3u8 files and skipped.')

        if len(added_tracks) == 0:
            context.summary.append(f'  No tracks to export.')
        else:
            if len(file_names) == 1:
                context.summary.append(f'  {len(added_tracks)} tracks written to m3u8 file (path: "{path}").')
            else:
                context.summary.append(
                    f'  {len(added_tracks)} tracks written to {len(file_names)} m3u8 files (path: "{path}").')

    click.echo('\n------------------------------------------------------------')
    click.echo('\n'.join(context.summary))
