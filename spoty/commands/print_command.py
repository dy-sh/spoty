from spoty import settings
from spoty import log
from spoty.utils import SpotyContext
import spoty.utils
import click


@click.command("print")
@click.option('--grouping-pattern', '--gp', show_default=True,
              default=settings.SPOTY.DEFAULT_DEST_GROUPING_PATTERN,
              help='Playlists will be named according to this pattern.')
@click.option('--print-pattern', '--pp', show_default=True,
              default=settings.SPOTY.DEFAULT_DEST_PRINT_PATTERN,
              help='Print a list of tracks according to this formatting pattern.')
@click.pass_obj
def print_tracks(context: SpotyContext,
                 grouping_pattern,
                 print_pattern,
                 ):
    """
Print a list of tracks to console.
    """

    tags_list = context.tags_list


    spoty.utils.print_tags_list(tags_list, print_pattern, grouping_pattern)

    grouped_tags = spoty.utils.group_tags_by_pattern(tags_list, grouping_pattern)
    context.summary.append(f'{len(tags_list)} tracks collected in {len(grouped_tags)} groups and printed to console')
    click.echo('\n------------------------------------------------------------')
    click.echo('\n'.join(context.summary))
