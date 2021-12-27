from spoty import settings
from spoty import log
from spoty.utils import SpotyContext
import spoty.utils
import click


@click.command("print")
@click.option('--print-pattern', '--pp', show_default=True,
              help='Print a list of tracks according to this formatting pattern. If not specified, DUPLICATE_PRINT_PATTERN setting from the config file will be used.')
@click.pass_obj
def print_duplicates(context: SpotyContext,
                     print_pattern,
                     ):
    """
Print a list of duplicates to console.
    """

    for i, group in enumerate(context.duplicates_groups):
        click.echo()
        click.echo(f"--------------------------- GROUP {i+1}/{len(context.duplicates_groups)} ---------------------------")
        if len(group.source_tags.items())>0:
            click.echo("Source:")
            spoty.utils.print_duplicates_tags_list([group.source_tags], print_pattern)

        if len(group.def_duplicates) > 0:
            click.echo("Duplicates:")
            spoty.utils.print_duplicates_tags_list(group.def_duplicates, print_pattern)

        if len(group.prob_duplicates) > 0:
            click.echo("Probably duplicates:")
            spoty.utils.print_duplicates_tags_list(group.prob_duplicates, print_pattern)


    click.echo('\n------------------------------------------------------------')
    click.echo('\n'.join(context.summary))
