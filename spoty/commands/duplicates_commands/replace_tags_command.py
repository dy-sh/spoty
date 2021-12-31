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

class TagsToReplace:
    source_tags:dict
    dest_tags:dict
    tags_keys:list

    def __init__(self):
        self.source_tags = {}
        self.dest_tags = {}
        self.tags_keys = []


@click.command("replace-tags")
@click.argument('tags')
@click.option('--confirm', '-y', is_flag=True,
              help='Do not ask for confirmation')
@click.pass_obj
def replace_tags(context: SpotyContext,
                     tags,
                     confirm
                     ):
    """
Get the specified tags from the tracks in the first list and write those tags to the tracks in the second list.

TAGS - Which tags to rewrite (specify separated by commas).
    """


    write_tags = tags.split(',')

    tags_to_update_list = []
    with click.progressbar(context.duplicates_groups, label='Collecting tags') as bar:
        for group in bar:
            # collect all tags
            for dup_tags in group.def_duplicates:
                if 'SPOTY_FILE_NAME' in dup_tags: # is local file
                    tags_keys=[]
                    for tag in write_tags:
                        if (tag in group.source_tags and tag not in dup_tags) \
                            or (tag not in group.source_tags and tag in dup_tags) \
                                or (tag in group.source_tags and tag in dup_tags and dup_tags[tag] != group.source_tags[tag]):
                            tags_keys.append(tag)
                    if len(tags_keys)>0:
                        t = TagsToReplace()
                        t.source_tags=group.source_tags
                        t.dest_tags = dup_tags
                        t.tags_keys=tags_keys
                        tags_to_update_list.append(t)

            for dup_tags in group.prob_duplicates:
                if 'SPOTY_FILE_NAME' in dup_tags:  # is local file
                    tags_keys=[]
                    for tag in write_tags:
                        if (tag in group.source_tags and tag not in dup_tags) \
                            or (tag not in group.source_tags and tag in dup_tags) \
                                or (tag in group.source_tags and tag in dup_tags and dup_tags[tag] != group.source_tags[tag]):
                            tags_keys.append(tag)
                    if len(tags_keys)>0:
                        t = TagsToReplace()
                        t.source_tags=group.source_tags
                        t.dest_tags = dup_tags
                        t.tags_keys=tags_keys
                        tags_to_update_list.append(t)

    if len(tags_to_update_list) == 0:
        click.echo("No tags to update found.")
        exit()

    click.echo('Next audio files will be edited:')

    for t in tags_to_update_list:
        click.echo(f'  {t.dest_tags["SPOTY_FILE_NAME"]}:')
        for tag in t.tags_keys:
            was = t.dest_tags[tag] if tag in t.dest_tags else ""
            new = t.source_tags[tag] if tag in t.source_tags else ""
            click.echo(f'    {tag} was "{was}", will become "{new}"')

    if not confirm:
        click.confirm(f'Are you sure you want to edit tags in {len(tags_to_update_list)} audio files?', abort=True)

    with click.progressbar(tags_to_update_list, label=f'Writing tags in {len(tags_to_update_list)} files') as bar:
        for t in bar:
            new_tags={}
            for tag in t.tags_keys:
                new = t.source_tags[tag] if tag in t.source_tags else ""
                new_tags[tag] = new
            spoty.audio_files.write_audio_file_tags(t.dest_tags['SPOTY_FILE_NAME'], new_tags)

    context.summary.append('Replacing tags:')
    context.summary.append(f'  {len(tags_to_update_list)} audio files edited.')

    click.echo('\n------------------------------------------------------------')
    click.echo('\n'.join(context.summary))
