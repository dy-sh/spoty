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
    context.summary.append(f'Counting:')

    for i, tags_list in enumerate(context.tags_lists):
        grouped_tags = spoty.utils.group_tags_by_pattern(tags_list, grouping_pattern)

        if len(context.tags_lists) > 1:
            context.summary.append(f'  --- List {i + 1}:')

        context.summary.append(f'  {len(tags_list)} tracks.')

        if len(grouped_tags) > 0:
            context.summary.append(f'  {len(grouped_tags)} groups by pattern.')

    if len(context.duplicates_groups) > 0:
        all_def_list = []
        all_prob_list = []
        all_source_list = []
        for group in context.duplicates_groups:
            all_def_list.append(group.source_tags)
            all_source_list.extend(group.def_duplicates)
            all_prob_list.extend(group.prob_duplicates)
        context.summary.append(f'  {len(all_source_list)} duplicate groups.')
        context.summary.append(f'  {len(all_def_list)} definitely duplicates.')
        context.summary.append(f'  {len(all_prob_list)} probably duplicates.')

    click.echo('\n------------------------------------------------------------')
    click.echo('\n'.join(context.summary))
