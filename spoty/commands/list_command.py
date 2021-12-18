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
              help='Read tracks in this spotify user library. To request a list for the current user, leave this option empty, or use "me" as ID.')
# @click.option('--source-deezer-playlist', '--sdp', multiple=True,
#               help='Read tracks in specified deezer playlist.')
# @click.option('--source-deezer-user', '--sdu', multiple=True,
#               help='Read tracks in this spotify user library.')
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
@click.option('--print', '-p', 'print_to_console', is_flag=True,
              help='Print a list of read tracks to console.')
@click.option('--print-tags', '--pt', default='ISRC,ARTIST,TITLE',
              help='Print this track tags.')
@click.option('--export-csv-playlists', '-e', is_flag=True,
              help='Export a list of read tracks to csv playlists.')
@click.option('--export-path', '--ep', default="./PLAYLISTS",
              help='The path on disk where to export csv-playlists.')
@click.option('--export-naming-pattern', '--enp', default='%SPOTY_PLAYLIST_NAME%',
              help='Exported playlists will be named according to this pattern.')
@click.option('--overwrite', '-o', is_flag=True,
              help='Overwrite existing csv playlists without asking')
@click.option('--timestamp', '-t', is_flag=True,
              help='Create a new subfolder with the current date and time for saved csv playlists')
def list(sources,
         source_spotify_playlist,
         source_spotify_user,
         # source_deezer_playlist,
         # source_deezer_user,
         source_local_files,
         source_local_playlists,
         filter_playlists_names,
         filter_tracks_tags,
         filter_tracks_no_tags,
         no_recursive,
         print_to_console,
         print_tags,
         export_csv_playlists,
         export_path,
         export_naming_pattern,
         overwrite,
         timestamp
         ):
    """
    List of tracks.

    \b
    SOURCES - List of local files paths or music services URIs.
        This argument is optional. Instead, you can pass parameters as --source options.
        Unlike --source options, the SRC argument accepts only the path to local files or the full URI to playlist.
        The --source options can also accept the ID of the playlist on a music service.

    \b
    Examples:
        Display number of tracks in the current spotify user playlists:
        spoty list --ssu

        Display all tracks and numver of tracks in the current spotify user playlists:
        spoty list --ssu -p

        Export all current spotify user playlists to default (./PLAYLISTS) path (overwrite files if already exist):
        spoty list --ssu -eo

        Export all current spotify user playlists to default path, overwrite files and display them to console:
        spoty list --ssu -peo

    """

    if len(source_spotify_user)==0 \
            and len(source_spotify_playlist)==0 \
            and len(source_local_files) == 0 \
            and len(source_local_playlists) == 0 \
            and len(sources) == 0:
        list(['list','--help'])
        exit()

    source_spotify_playlist = to_list(source_spotify_playlist)
    source_spotify_user = to_list(source_spotify_user)
    # source_deezer_playlist = to_list(source_deezer_playlist)
    # source_deezer_user = to_list(source_deezer_user)
    source_local_files = to_list(source_local_files)
    source_local_playlists = to_list(source_local_playlists)
    filter_playlists_names = to_list(filter_playlists_names)
    filter_tracks_tags = to_list(filter_tracks_tags)
    filter_tracks_no_tags = to_list(filter_tracks_no_tags)
    print_tags = print_tags.split(',')

    for source in sources:
        if spoty.spotify.check_is_playlist_URI(source):
            source_spotify_playlist.append(source)
        elif spoty.csv_playlist.is_csv(source):
            source_local_playlists.append(source)
        elif spoty.utils.is_valid_path(source):
            source_local_files.append(source)
        else:
            click.echo(f'Cant recognize source: "{source}"', err=True)

    all_tags = []

    tracks, tags = spoty.spotify.get_tracks_from_spotify_playlists(
        source_spotify_playlist, filter_playlists_names, filter_tracks_tags, filter_tracks_no_tags)
    all_tags.extend(tags)

    tracks, tags = spoty.spotify.get_tracks_of_spotify_user(
        source_spotify_user, filter_playlists_names, filter_tracks_tags, filter_tracks_no_tags)
    all_tags.extend(tags)

    file_names, tags = spoty.local_files.get_tracks_from_local_paths(
        source_local_files, not no_recursive, filter_tracks_tags, filter_tracks_no_tags)
    all_tags.extend(tags)

    playlists, tags = spoty.csv_playlist.get_tracks_from_local_paths(
        source_local_playlists, not no_recursive, filter_tracks_tags, filter_tracks_no_tags)
    all_tags.extend(tags)

    if print_to_console:
        spoty.utils.print_tracks(all_tags, print_tags)

    click.echo(f'Total tracks found: {len(all_tags)}')

    if export_csv_playlists:
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
