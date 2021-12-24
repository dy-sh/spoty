from spoty import settings
from spoty import log
from spoty.utils import SpotyContext
import spoty.utils
import click


@click.command("count")
@click.option('--grouping-pattern', '--gp', show_default=True,
              default=settings.SPOTY.DEFAULT_GROUPING_PATTERN,
              help='Tracks will be grouped to playlists according to this pattern.')
@click.pass_obj
def count_tracks(context: SpotyContext,
                 grouping_pattern,
                 ):
    """
Print a number of tracks to console.
    """

    for i, tags_list in enumerate(context.tags_lists):
        grouped_tags = spoty.utils.group_tags_by_pattern(tags_list, grouping_pattern)

        if len(context.tags_lists) == 1:
            if len(grouped_tags) == 0:
                context.summary.append(f'Total {len(tags_list)} tracks.')
            else:
                context.summary.append(f'Total {len(tags_list)} tracks grouped into {len(grouped_tags)} playlists.')
        else:
            if len(grouped_tags) == 0:
                context.summary.append(f'List {i+1}: Total {len(tags_list)} tracks.')
            else:
                context.summary.append(f'List {i+1}: Total {len(tags_list)} tracks grouped into {len(grouped_tags)} playlists.')

    click.echo('\n------------------------------------------------------------')
    click.echo('\n'.join(context.summary))
