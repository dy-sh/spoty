from spoty import settings
from spoty import log
import spoty.spotify_api
import spoty.csv_playlist
import spoty.utils
from spoty.utils import SpotyContext
import click
import os
from datetime import datetime


@click.command("sync-spotify")
@click.option('--grouping-pattern', '--gp', show_default=True,
              default=settings.SPOTY.DEFAULT_GROUPING_PATTERN,
              help='Tracks will be grouped to playlists according to this pattern.')
@click.option('--confirm', '-y', is_flag=True,
              help='Confirm all questions with a positive answer automatically.')
@click.option('--ignore-duration', '-i', is_flag=True,
              help='Dont match track duration')
@click.option('--export-result', '-r', is_flag=True,
              help='Export csv files with result (imported, not found, skipped tracks)')
@click.option('--result-path', '--rp', show_default=True,
              default=settings.SPOTY.DEFAULT_EXPORT_PATH,
              help='Path to create resulting csv files')
@click.option('--source-playlist-prefix', '--spp',
              help='Source playlist names prefix. Only source playlists with names starting with the specified string will be synchronized.')
@click.option('--playlist-prefix', '--pp', show_default=True,
              default=settings.SPOTY.DEFAULT_SYNC_PLAYLIST_PREFIX,
              help='Spotify playlist names prefix. Only Spotify playlists with names starting with the specified string will be synchronized.')
@click.pass_obj
def sync_spotify(context: SpotyContext,
                 grouping_pattern,
                 confirm,
                 ignore_duration,
                 export_result,
                 result_path,
                 source_playlist_prefix,
                 playlist_prefix
                 ):
    """
Sync tracks to Spotify playlists.

\b
When synchronizing, new playlists will be created that are not in the library.
Playlists that already exist will be updated (new tracks are added and non-existent ones are removed).
If a playlist exists in Spotify, but is not present in the source, then such a playlist will be removed from Spotify.
That is why it is advisable to use some kind of prefix in the names of the playlists that will be syncronized.
To do this, use the option --playlist-prefix.
When you use a --playlist-prefix, only playlists with names starting with this prefix will be updated or deleted as a result of synchronization.
If you leave the prefix empty, as a result, all playlists in the library will participate in synchronization, and may be deleted if playlists with the same names are not in the source list.
To avoid accidentally deleting any playlists, the prefix is set by default in the config file. You can override it there, or with --playlist-prefix option.

\b
Playlist names are generated based on the --grouping-pattern.
By default, the pattern is set in the configuration file, but you can override it using the --grouping-pattern option.
For example, if you set the pattern as "%SPOTY_PLAYLIST_NAME%", then the folder name will be used as the playlist name for local audio files.
You can read more about --grouping-pattern in the general Spoty help (spoty --help).

\b
There is also an option --source-playlist-prefix. By default, this option is not used.
By specifying this option, you will filter the playlists in the source track list, leaving only those that start with the specified prefix.
In addition, this prefix will be stripped from the source playlist name during synchronization.
This can be used to sync playlists between different music services or different accounts.

\b
Let's look at an example.
Initially, you had local files and grouped them into playlists by genre using the following command:
  spoty get --a "./music" sync-spotify --gp "%GENRE%" --pp "#SYNC "
As a result, you got the following spotify playlists:
"#SYNC Pop", "#SYNC Rock", "#SYNC Jazz"
Next, you wanted to sync these playlists with another account. Logged into another account, and did sync as follows:
  spoty get --s "MY_FIRST_ACCOUNT_NAME" sync-spotify --gp "%SPOTY_PLAYLIST_NAME%" --pps "#SYNC " --pp "#SYNC "
As a result of this command, you will get an exact copy of the playlists with the same names in another account.
If you remove --pps option, you will get "#SYNC #SYNC Pop", "#SYNC #SYNC Rock", "#SYNC #SYNC Jazz" playlists in the second account.
    """

    if source_playlist_prefix is None:
        source_playlist_prefix = ""
    if playlist_prefix is None:
        playlist_prefix = ""

    for tags_list in context.tags_lists:

        found_tags_list, not_found_tags_list = spoty.spotify_api.find_missing_track_ids(tags_list, ignore_duration)

        click.echo('Next playlists will be synced to Spotify library:')
        grouped_tags = spoty.utils.group_tags_by_pattern(found_tags_list, grouping_pattern)

        new_groups = {}
        for group_name, tags_l in grouped_tags.items():
            if group_name.startswith(source_playlist_prefix):
                new_group_name = group_name[len(source_playlist_prefix):]
                new_group_name = playlist_prefix + new_group_name
                new_groups[new_group_name] = tags_l
        grouped_tags = new_groups

        for group_name, g_tags_list in grouped_tags.items():
            click.echo("  " + group_name)
        click.echo(f'Total {len(found_tags_list)} tracks in {len(grouped_tags)} playlists.')

        if not confirm:
            if click.confirm(f'\nDo you want to continue?'):
                click.echo("")  # for new line
            else:
                click.echo("\nCanceled.")
                exit()

        playlist_ids, imported_tags_list, source_duplicates_tags_list, already_exist_tags_list = \
            spoty.spotify_api.import_playlists_from_tag_groups(grouped_tags, True, False, False, confirm)

        deleted_playlists=[]
        playlists = spoty.spotify_api.get_list_of_playlists()
        for playlist in playlists:
            if playlist['name'].startswith(playlist_prefix):
                if playlist['name'] not in grouped_tags.keys():
                    res = spoty.spotify_api.delete_playlist(playlist['id'], confirm)
                    if res:
                        deleted_playlists.append(playlist)

        # create result csv playlists

        if export_result:
            result_path = os.path.abspath(result_path)
            date_time_str = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
            result_path = os.path.join(result_path, 'import-spotify-' + date_time_str)

            if len(imported_tags_list) > 0:
                path = os.path.join(result_path, 'added')
                spoty.csv_playlist.create_csvs(imported_tags_list, path, playlist_prefix + grouping_pattern)
            if len(source_duplicates_tags_list) > 0:
                path = os.path.join(result_path, 'skipped_source_duplicates')
                spoty.csv_playlist.create_csvs(source_duplicates_tags_list, path, playlist_prefix + grouping_pattern)
            if len(already_exist_tags_list) > 0:
                path = os.path.join(result_path, 'skipped_already_exist')
                spoty.csv_playlist.create_csvs(already_exist_tags_list, path, playlist_prefix + grouping_pattern)
            if len(not_found_tags_list) > 0:
                path = os.path.join(result_path, 'not_found')
                spoty.csv_playlist.create_csvs(not_found_tags_list, path, playlist_prefix + grouping_pattern)

        # print summery

        context.summary.append("Sync to Spotify:")
        if len(source_duplicates_tags_list) > 0:
            context.summary.append(f'  {len(source_duplicates_tags_list)} duplicates in collected tracks skipped.')
        if len(already_exist_tags_list) > 0:
            context.summary.append(f'  {len(already_exist_tags_list)} tracks already exist in playlists and skipped.')
        if len(not_found_tags_list) > 0:
            context.summary.append(f'  {len(not_found_tags_list)} tracks not found by tags.')
        if len(deleted_playlists) > 0:
            context.summary.append(f'  {len(deleted_playlists)} playlists deleted.')

        if len(imported_tags_list) == 0:
            context.summary.append(f'  No new tracks found.')
        else:
            context.summary.append(
                    f'  {len(imported_tags_list)} new tracks added.')

    click.echo('\n------------------------------------------------------------')
    click.echo('\n'.join(context.summary))
