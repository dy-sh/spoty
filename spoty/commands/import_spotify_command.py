from spoty import settings
from spoty import log
import spoty.spotify_api
import spoty.utils
from spoty.utils import SpotyContext
import click


@click.command("import-spotify")
@click.option('--grouping-pattern', '--gp', show_default=True,
              default=settings.SPOTY.DEFAULT_GROUPING_PATTERN,
              help='Tracks will be grouped to playlists according to this pattern.')
@click.option('--duplicates', '-d', type=bool, is_flag=True, default=False,
              help='Allow duplicates (add tracks that are already exist in the playlist).')
@click.option('--append', '-a', is_flag=True,
              help='Add tracks to an existing playlist if already exists. If this option is not specified, a new playlist will always be created.')
@click.option('--overwrite', '-o', is_flag=True,
              help='Overwrite existing playlist')
# @click.option('--duplicates-compare-tags', '--dct', show_default=True,
#               default=settings.SPOTY.DEFAULT_COMPARE_TAGS,
#               help='Compare duplicates by this tags. It is optional. You can also change the list of tags in the config file.')
@click.option('--yes-all', '-y', is_flag=True,
              help='Confirm all questions with a positive answer automatically.')
@click.pass_obj
def import_spotify(context: SpotyContext,
                   grouping_pattern,
                   duplicates,
                   append,
                   overwrite,
                   # duplicates_compare_tags,
                   yes_all,
                   ):
    """
Import track list to Spotify Library
    """

    tags_list = context.tags_list

    if append and overwrite:
        click.echo(f'Simultaneous use of "--append" and "--overwrite" is not possible',
                   err=True)
        exit()

    click.echo('Next playlists will be imported to Spotify library:')
    grouped_tags = spoty.utils.group_tags_by_pattern(tags_list, grouping_pattern)
    for group_name, g_tags_list in grouped_tags.items():
        click.echo("  " + group_name)
    click.echo(f'Total {len(tags_list)} tracks in {len(grouped_tags)} playlists.')

    if not yes_all:
        if click.confirm(f'Do you want to continue?'):
            click.echo("")  # for new line
        else:
            click.echo("\nCanceled.")
            exit()

    playlist_ids, added_tracks, import_duplicates, already_exist, not_found_tracks = \
        spoty.spotify_api.import_playlists_from_tags_list(
            tags_list, grouping_pattern, overwrite, append, duplicates, yes_all)

    # print summery

    context.summary.append(f'{len(added_tracks)} tracks imported in {len(playlist_ids)} Spotify playlists.')
    if len(import_duplicates) > 0:
        context.summary.append(f'{len(import_duplicates)} duplicates in collected tracks skipped.')
    if len(already_exist) > 0:
        context.summary.append(f'{len(already_exist)} tracks already exist in playlists and skipped.')
    if len(not_found_tracks) > 0:
        context.summary.append(f'{len(not_found_tracks)} tracks not found by tags.')

    click.echo('\n------------------------------------------------------------')
    click.echo('\n'.join(context.summary))
