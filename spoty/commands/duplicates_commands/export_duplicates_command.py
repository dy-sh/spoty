from spoty import settings
from spoty import log
from spoty.utils import SpotyContext
import spoty.utils
import spoty.csv_playlist
import click
import os
from datetime import datetime


@click.command("export")
@click.option('--path', '--p', show_default=True,
              default=settings.SPOTY.DEFAULT_EXPORT_PATH,
              help='The path on disk where to export csv files.')
@click.option('--no-source', '-s', is_flag=True,
              help='Do not include source tracks')
@click.option('--no-split-groups', '-g', is_flag=True,
              help='Do not add empty line between groups')
@click.pass_obj
def export_duplicates(context: SpotyContext,
                      path,
                      no_source,
                      no_split_groups
                      ):
    """
Export a list of duplicates to csv file.
    """

    # export result to  csv files
    path = os.path.abspath(path)
    date_time_str = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    file_name = 'duplicates-' + date_time_str

    all_tags_list = []
    for group in context.duplicates_groups:
        if not no_source:
            all_tags_list.extend(group.source_def_duplicates)
            all_tags_list.extend(group.source_prob_duplicates)
        all_tags_list.extend(group.dest_def_duplicates)
        all_tags_list.extend(group.dest_prob_duplicates)
        if not no_split_groups:
            all_tags_list.append({})

    spoty.csv_playlist.create_csvs(all_tags_list, path, file_name)

    click.echo('\n------------------------------------------------------------')
    click.echo('\n'.join(context.summary))
