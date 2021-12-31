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
@click.option('--confirm', '-y', is_flag=True,
              help='Do not ask for confirmation')
@click.pass_obj
def add_missing_tags(context: SpotyContext,
                     confirm
            ):
    """
Collect tags from all duplicated tracks and add missing tags (update them all).
    """

    tags_to_add={}
    with click.progressbar(context.duplicates_groups, label='Collecting missing tags') as bar:
        for group in bar:
            # collect all tags
            all_group_tags=group.source_tags.copy()
            for tags in group.def_duplicates:
                new_tags = spoty.utils.get_missing_tags(all_group_tags, tags)
                for key,value in new_tags.items():
                    all_group_tags[key]=value
            for tags in group.prob_duplicates:
                new_tags = spoty.utils.get_missing_tags(all_group_tags, tags)
                for key,value in new_tags.items():
                    all_group_tags[key]=value

            # find missing tags
            if 'SPOTY_FILE_NAME' in group.source_tags: # is local file
                new_tags = spoty.utils.get_missing_tags(group.source_tags, all_group_tags)
                if len(new_tags.keys()) > 0:
                    tags_to_add[group.source_tags['SPOTY_FILE_NAME']] = new_tags
            for tags in group.def_duplicates:
                if 'SPOTY_FILE_NAME' in tags: # is local file
                    new_tags = spoty.utils.get_missing_tags(tags,all_group_tags)
                    if len(new_tags.keys())>0:
                        tags_to_add[tags['SPOTY_FILE_NAME']]=new_tags
            for tags in group.prob_duplicates:
                if 'SPOTY_FILE_NAME' in tags: # is local file
                    new_tags = spoty.utils.get_missing_tags(tags,all_group_tags)
                    if len(new_tags.keys())>0:
                        tags_to_add[tags['SPOTY_FILE_NAME']]=new_tags

    if len(tags_to_add.items()) == 0:
        click.echo("No missing tags found")
        exit()

    click.echo('Next audio files will be edited:')

    for file_name, tags in tags_to_add.items():
        click.echo(f'  {file_name}:\n    {",".join(tags.keys())}')



    if not confirm:
        click.confirm(f'Are you sure you want to edit tags in {len(tags_to_add.items())} audio files?', abort=True)

    with click.progressbar(tags_to_add.items(), label=f'Writing tags in {len(tags_to_add.items())} files') as bar:
        for file_name, tags in bar:
            spoty.audio_files.write_audio_file_tags(file_name, tags)

    context.summary.append('Adding missing tags:')
    context.summary.append(f'  {len(tags_to_add.items())} audio files edited.')


    click.echo('\n------------------------------------------------------------')
    click.echo('\n'.join(context.summary))
