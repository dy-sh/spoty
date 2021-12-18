from spoty import settings
from spoty import log
import spoty.spotify
import spoty.local_files
import spoty.csv_playlist
import spoty.utils
import click
import re
import time
import os
from datetime import datetime


@click.command("list")
@click.argument('sources', nargs=-1)
@click.option('--source-spotify-playlist', '--ssp', multiple=True,
              help='Read tracks in specified spotify playlist.')
@click.option('--source-spotify-user', '--ssu', multiple=True, is_flag=False, flag_value="me",
              help='Read tracks in this spotify user library. If no user ID is specified, the current user will be used.')
@click.option('--source-deezer-playlist', '--sdp', multiple=True,
              help='Read tracks in specified deezer playlist.')
@click.option('--source-deezer-user', '--sdu', multiple=True,
              help='Read tracks in this spotify user library.')
@click.option('--source-local-files', '--slf', multiple=True,
              help='Read tracks from local files in specified path.')
@click.option('--source-local-playlists', '--slp', multiple=True,
              help='Read tracks from local csv playlists in specified path.')
@click.option('--filter-playlists-names', '--fpn', multiple=True,
              help='Read only playlists whose names matches this regex filter')
@click.option('--filter-tracks-tags', '--ftt', multiple=True,
              help='Get only tracks that have all of the specified tags.')
@click.option('--filter-tracks-no-tags', '--ftnt', multiple=True,
              help='Get only tracks that do not have any of the listed tags.')
@click.option('--no-recursive', '-r', is_flag=True,
              help='Do not search in subdirectories from the specified path.')
@click.option('--count', '-c', is_flag=True,
              help='Print number of tracks read to console.')
@click.option('--print', '-p', 'print_to_console', is_flag=True,
              help='Print a list of read tracks to console.')
@click.option('--export-path', '--ep',
              help='Export a list of read tracks to csv playlists in specified path.')
@click.option('--export-naming-pattern', '--enp', default='%SPOTY_PLAYLIST_NAME%',
              help='Exported playlists will be named according to this pattern.')
@click.option('--overwrite', '-o', is_flag=True,
              help='Overwrite existing csv playlists without asking')
@click.option('--timestamp', '-t', is_flag=True,
              help='Create a new subfolder with the current date and time for saved csv playlists')
def list(sources,
         source_spotify_playlist,
         source_spotify_user,
         source_deezer_playlist,
         source_deezer_user,
         source_local_files,
         source_local_playlists,
         filter_playlists_names,
         filter_tracks_tags,
         filter_tracks_no_tags,
         no_recursive,
         count,
         print_to_console,
         export_path,
         export_naming_pattern,
         overwrite,
         timestamp
         ):
    r"""
    List of tracks.

    \b
    SOURCES - List of local files paths or music services URIs.
    This argument is optional. Instead, you can pass parameters as --source options.
    Unlike --source options, the SRC argument accepts only the path to local files or the full URI to playlist.
    The --source options can also accept the ID of the playlist on a music service.

    Examples:
        spoty list -c https://open.spotify.com/playlist/7E6SNhIGjSqEmzHISqnMrJ https://open.spotify.com/playlist/7E45634fjSqEmzHISqnMrJ

        spoty list -c --ssp 0yRgrCdkntJG83mFbFvrBP --ssp https://open.spotify.com/playlist/7E6SNhIGjSqEmzHISqnMrJ

    """

    if export_path == None and not print_to_console and not count:
        click.echo("Please, specify what to do with the read files:\n" +
                   "-p, to printing the list to the console.\n" +
                   "--ep [PATH], to export the list to the csv files.\n"
                   "-c, to count the number of tracks and print to the console.")
        exit()

    source_spotify_playlist = to_list(source_spotify_playlist)
    source_spotify_user = to_list(source_spotify_user)
    source_deezer_playlist = to_list(source_deezer_playlist)
    source_deezer_user = to_list(source_deezer_user)
    source_local_files = to_list(source_local_files)
    source_local_playlists = to_list(source_local_playlists)
    filter_playlists_names = to_list(filter_playlists_names)
    filter_tracks_tags = to_list(filter_tracks_tags)
    filter_tracks_no_tags = to_list(filter_tracks_no_tags)

    all_tags = []

    for source in sources:
        if spoty.spotify.check_is_playlist_URI(source):
            source_spotify_playlist.append(source)
        elif spoty.csv_playlist.is_csv(source):
            source_local_playlists.append(source)
        elif spoty.utils.is_valid_path(source):
            source_local_files.append(source)
        else:
            click.echo(f'Cant recognize source: "{source}"', err=True)

    spotify_tracks, spotify_tags = spoty.spotify.get_tracks_from_spotify_playlists(
        source_spotify_playlist, filter_playlists_names, filter_tracks_tags, filter_tracks_no_tags)
    all_tags.extend(spotify_tags)

    spotify__user_tracks, spotify_user_tags = spoty.spotify.get_tracks_of_spotify_user(
        source_spotify_user, filter_playlists_names, filter_tracks_tags, filter_tracks_no_tags)
    all_tags.extend(spotify_user_tags)


    local_file_names, local_tags = spoty.local_files.get_tracks_from_local_path(
        source_local_files, no_recursive, filter_tracks_tags, filter_tracks_no_tags)
    all_tags.extend(local_tags)



    if print_to_console:
        for i, track in enumerate(spotify_tags):
            click.echo(
                f'--------------------- SPOTIFY TRACK {i + 1} / {len(spotify_tags)} ---------------------')
            spoty.utils.print_track_main_tags(track)
        for i, track in enumerate(local_tags):
            click.echo(
                f'--------------------- LOCAL TRACK {i + 1} / {len(local_tags)} ---------------------')
            spoty.utils.print_track_main_tags(track)

        if len(all_tags) > 0:
            click.echo("-------------------------------------------------------------------------------------")

    if count:
        click.echo(f'Total tracks: {len(all_tags)}')



    if export_path is not None:
        if timestamp:
            now = datetime.now()
            date_time_str = now.strftime("%Y_%m_%d-%H_%M_%S")
            export_path = os.path.join(export_path, date_time_str)

        exported_playlists_file_names, exported_playlists_names, exported_tracks = \
            spoty.csv_playlist.export_tags(all_tags, export_path, export_naming_pattern, overwrite)


def to_list(some_tuple):
    l = []
    l.extend(some_tuple)
    return l



