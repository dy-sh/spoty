from spoty import settings
from spoty import log
import spoty.deezer_api
import spoty.csv_playlist
import spoty.deezer_api
import spoty.spotify_api
import spoty.audio_files
import spoty.utils
from spoty.commands import get_group
from spoty.utils import SpotyContext
from spoty.utils import DuplicatesGroup
import click
import os
from datetime import datetime


@click.command("add-missing-tags")
@click.option('--tags', '--t',
              help='Which tags to search (specify separated by commas). If not specified, will search all tags.')
@click.option('--ignore-tags', '--T',
              help='Which tags to ignore (specify separated by commas).',
              default=settings.SPOTY.DEFAULT_IGNORE_MISSING_TAGS)
@click.option('--confirm', '-y', is_flag=True,
              help='Do not ask for confirmation.')
@click.option('--from-second-too', '-s', is_flag=True,
              help='Collect tags from tracks in second list too (from duplicates).')
@click.option('--to-first-too', '-f', is_flag=True,
              help='Write missing tags to tracks from first list too.')
@click.pass_obj
def add_missing_tags(context: SpotyContext,
                     tags,
                     ignore_tags,
                     confirm,
                     from_second_too,
                     to_first_too
                     ):
    """
Collect tags from all duplicated tracks and add missing tags (update them all).
    """
    context.summary.append('Adding missing tags:')

    compare_tags = tags.split(',') if tags is not None else []
    for i in range(len(compare_tags)):
        compare_tags[i] = compare_tags[i].upper()

    ignore_tags = ignore_tags.split(',') if ignore_tags is not None else []
    for i in range(len(ignore_tags)):
        ignore_tags[i] = ignore_tags[i].upper()

    tags_to_add = {}
    with click.progressbar(context.duplicates_groups, label='Collecting missing tags') as bar:
        for group in bar:
            # collect all tags
            all_group_tags = group.source_tags.copy()
            if from_second_too:
                for tags in group.def_duplicates:
                    new_tags = spoty.utils.get_missing_tags(all_group_tags, tags, compare_tags,ignore_tags)
                    for key, value in new_tags.items():
                        all_group_tags[key] = value
                for tags in group.prob_duplicates:
                    new_tags = spoty.utils.get_missing_tags(all_group_tags, tags, compare_tags,ignore_tags)
                    for key, value in new_tags.items():
                        all_group_tags[key] = value

            # find missing tags
            if to_first_too:
                if 'SPOTY_FILE_NAME' in group.source_tags:  # is local file
                    new_tags = spoty.utils.get_missing_tags(group.source_tags, all_group_tags, compare_tags,ignore_tags)
                    if len(new_tags.keys()) > 0:
                        tags_to_add[group.source_tags['SPOTY_FILE_NAME']] = new_tags
            for tags in group.def_duplicates:
                if 'SPOTY_FILE_NAME' in tags:  # is local file
                    new_tags = spoty.utils.get_missing_tags(tags, all_group_tags, compare_tags,ignore_tags)
                    if len(new_tags.keys()) > 0:
                        tags_to_add[tags['SPOTY_FILE_NAME']] = new_tags
            for tags in group.prob_duplicates:
                if 'SPOTY_FILE_NAME' in tags:  # is local file
                    new_tags = spoty.utils.get_missing_tags(tags, all_group_tags, compare_tags,ignore_tags)
                    if len(new_tags.keys()) > 0:
                        tags_to_add[tags['SPOTY_FILE_NAME']] = new_tags

    if len(tags_to_add.items()) == 0:
        context.summary.append("  No missing tags found")
    else:

        click.echo('Next audio files will be edited:')

        for file_name, tags in tags_to_add.items():
            click.echo(f'  {file_name}:\n    {",".join(tags.keys())}')

        if not confirm:
            click.confirm(f'Are you sure you want to edit tags in {len(tags_to_add.items())} audio files?', abort=True)

        with click.progressbar(tags_to_add.items(), label=f'Writing tags in {len(tags_to_add.items())} files') as bar:
            for file_name, tags in bar:
                spoty.audio_files.write_audio_file_tags(file_name, tags)

        context.summary.append(f'  {len(tags_to_add.items())} audio files edited.')

    click.echo('\n------------------------------------------------------------')
    click.echo('\n'.join(context.summary))
