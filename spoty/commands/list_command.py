from spoty import settings
from spoty import log
import spoty.spotify
import spoty.audio_files
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
@click.option('--source-audio', '--sa', multiple=True,
              help='Read tracks from audio files located in specified local path.')
@click.option('--source-csv', '--sc', multiple=True,
              help='Read tracks from csv playlists located in specified local path. You can specify the scv filename as well.')
@click.option('--filter-playlists-names', '--fpn',
              help='Read only playlists whose names matches this regex filter')
@click.option('--filter-have-tags', '--fht', multiple=True,
              help='Get only tracks that have all of the specified tags.')
@click.option('--filter-have-no-tags', '--fhnt', multiple=True,
              help='Get only tracks that do not have any of the listed tags.')
@click.option('--no-recursive', '-r', is_flag=True,
              help='Do not search in subdirectories from the specified path.')
@click.option('--print', '-p', 'print_to_console', is_flag=True,
              help='Print a list of read tracks to console.')
@click.option('--print-tags', '--pt', default='ISRC,ARTIST,TITLE',
              help='Print this track tags. Specify tags separated by commas.')
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
         source_audio,
         source_csv,
         filter_playlists_names,
         filter_have_tags,
         filter_have_no_tags,
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
SOURCES - List of sources where tracks will be read.
    As a source, the following can be used:
    - Path to local audio files (with or without recursion)
    - Path to local csv files (with or without recursion)
    - Name of csv file
    - Spotify playlist URI
    - Spotify user URI
    SOURCES argument is optional. Instead, you can pass parameters as --source options.
    For example, --source-spotify-playlist (--ssp) can take not only URI but also playlist ID (part of URI)

Examples:

\b
    Display the number of tracks in the playlists of the current Spotify user:
    spoty list --ssu

\b
    Displaying all tracks in the playlists of the current Spotify user:
    spoty list --ssu -p

\b
    Export all tracks of the current Spotify user to csv playlists in the default (./PLAYLISTS) path (overwrite files if they already exist):
    spoty list --ssu -eo

\b
    Combination of the two commands above:
    spoty list --ssu -peo

\b
    Displaying all tracks in the playlists whose names start with "BEST":
    spoty list -p --ssu --fpn "^BEST"

\b
    Display all tracks in two Spotify playlists:
    spoty list -p --ssp 37i9dQZF1DX12G1GAEuIuj --ssp 37i9dQZEVXbNG2KDcFcKOF

\b
    Same as above command:
    spoty list -p https://open.spotify.com/playlist/37i9dQZF1DX12G1GAEuIuj https://open.spotify.com/playlist/37i9dQZEVXbNG2KDcFcKOF

\b
    Display the number of tracks in Spotify playlist:
    spoty list https://open.spotify.com/playlist/37i9dQZF1DX12G1GAEuIuj

\b
    Display all tracks in two local paths:
    spoty list -p ./music ./music2

\b
    Display all tracks in local paths. The specified tags will be displayed.
    spoty list ./music -p --pt TITLE,ARTIST,DATE

\b
    Export all tracks from local paths to csv playlist:
    spoty list -pe ./music

\b
    Display all tracks in local paths that have the specified tags:
    spoty list ./music -p --fht "ISRC" --fht "BARCORE"

\b
    Display all tracks in local paths that do not have the specified tags:
    spoty list ./music -p --fhnt "TITLE"

\b
    Export all tracks from local paths to csv playlist in the specified path:
    spoty list -pe music --ep "./music playlists"

\b
    Display all tracks from csv playlists found in path "./PLAYLISTS":
    spoty list -p --sc "./PLAYLISTS"

\b
    Display all tracks from csv playlist:
    spoty list -p PLAYLISTS/BEST.csv

\b
    Note that if you specify a path as an argument without specifying that it is audio or a playlist (--sa or --sc), then both audio and playlists will be searched in this path:
    spoty list -p SOME_FOLDER



    """

    if len(source_spotify_user) == 0 \
            and len(source_spotify_playlist) == 0 \
            and len(source_audio) == 0 \
            and len(source_csv) == 0 \
            and len(sources) == 0:
        list(['list', '--help'])
        exit()

    source_spotify_playlist = to_list(source_spotify_playlist)
    source_spotify_user = to_list(source_spotify_user)
    # source_deezer_playlist = to_list(source_deezer_playlist)
    # source_deezer_user = to_list(source_deezer_user)
    source_audio = to_list(source_audio)
    source_csv = to_list(source_csv)
    filter_have_tags = to_list(filter_have_tags)
    filter_have_no_tags = to_list(filter_have_no_tags)
    print_tags = print_tags.split(',')

    # check sources

    source_csv_files=[]
    source_csv_paths=[]
    for source in source_csv:
        if spoty.csv_playlist.is_csv(source):
            source_csv_files.append(source)
        elif spoty.utils.is_valid_path(source):
            source_csv_paths.append(source)
        else:
            click.echo(f'Cant find csv source: "{source}"', err=True)
            exit()

    for source in source_audio:
        if not spoty.utils.is_valid_path(source):
            click.echo(f'Cant find audio path: "{source}"', err=True)
            exit()

    for source in sources:
        if spoty.spotify.check_is_playlist_URI(source):
            source_spotify_playlist.append(source)
        if spoty.spotify.check_is_playlist_URI(source):
            source_spotify_user.append(source)
        elif spoty.csv_playlist.is_csv(source):
            source_csv_files.append(source)
        elif spoty.utils.is_valid_path(source):
            source_audio.append(source)
            source_csv_paths.append(source)
        else:
            click.echo(f'Cant recognize source: "{source}"', err=True)

    all_tags = []

    spotify_playlists_tracks, tags = spoty.spotify.get_tracks_from_spotify_playlists(
        source_spotify_playlist, filter_playlists_names, filter_have_tags, filter_have_no_tags)
    all_tags.extend(tags)

    spotify_user_tracks, tags, spotify_user_playlists = spoty.spotify.get_tracks_of_spotify_user(
        source_spotify_user, filter_playlists_names, filter_have_tags, filter_have_no_tags)
    all_tags.extend(tags)

    audio_file_names = spoty.audio_files.find_audio_files_in_paths(
        source_audio, not no_recursive, filter_have_tags, filter_have_no_tags)
    tags = spoty.audio_files.read_audio_files_tags(audio_file_names)
    all_tags.extend(tags)

    csv_file_names = spoty.csv_playlist.find_csvs_in_paths(source_csv_paths, not no_recursive)
    csv_file_names.extend(source_csv_files)
    csv_tags = spoty.csv_playlist.read_tags_from_csvs(csv_file_names, filter_have_tags, filter_have_no_tags)
    all_tags.extend(csv_tags)

    if print_to_console:
        spoty.utils.print_tags_list(all_tags, print_tags)

    click.echo('-------------------------------------------------------------------------------------')
    print_total=False
    if len(spotify_playlists_tracks) > 0:
        click.echo(f'{len(spotify_playlists_tracks)} tracks found in {len(source_spotify_playlist)} spotify playlists.')
        if len(spotify_playlists_tracks)!=len(all_tags):
            print_total=True
    if len(spotify_user_tracks) > 0:
        if len(source_spotify_user)==1:
            click.echo(f'{len(spotify_user_tracks)} tracks found in {len(spotify_user_playlists)} playlists in spotify user library.')
        else:
            click.echo(f'{len(spotify_user_tracks)} tracks found in {len(spotify_user_playlists)} playlists in libraries of {len(source_spotify_user)} spotify users.')
        if len(spotify_user_tracks)!=len(all_tags):
            print_total=True
    if len(audio_file_names) > 0:
        click.echo(f'{len(audio_file_names)} audio files found in {len(source_audio)} local paths.')
        if len(audio_file_names)!=len(all_tags):
            print_total=True
    if len(csv_tags) > 0:
        click.echo(f'{len(csv_tags)} tracks found in {len(csv_file_names)} csv playlists.')
        if len(csv_tags)!=len(all_tags):
            print_total=True

    if print_total:
        click.echo(f'Total tracks found: {len(all_tags)}')

    if export_csv_playlists:
        if timestamp:
            now = datetime.now()
            date_time_str = now.strftime("%Y_%m_%d-%H_%M_%S")
            export_path = os.path.join(export_path, date_time_str)

        exported_playlists_file_names, exported_playlists_names, exported_tracks = \
            spoty.csv_playlist.create_csvs(all_tags, export_path, export_naming_pattern, overwrite)

        mess = f'\n{len(exported_tracks)} tracks exported to {len(exported_playlists_file_names)} playlists in path: "{export_path}"'
        click.echo(mess)


def to_list(some_tuple):
    l = []
    l.extend(some_tuple)
    return l
