from spoty.commands import count_command
from spoty.commands import print_command
from spoty.commands import export_command
from spoty.commands import import_spotify_command
from spoty.commands import filter_group
from spoty.utils import SpotyContext
from spoty import settings
from spoty import log
import spoty.spotify
import spoty.audio_files
import spoty.csv_playlist
import spoty.utils
import click
import time


@click.group("get")
@click.option('--spotify-playlist', '--sp', multiple=True,
              help='Get tracks from Spotify playlist URI or ID.')
@click.option('--spotify-entire-library', '--s', multiple=True,
              help='Get all tracks from Spotify library (by user URI or ID). To request a list for the current authorized user, use "me" as ID.')
@click.option('--spotify-entire-library-regex', '--sr', nargs=2, multiple=True,
              help='Works the same as --spotify-entire-library, but you can specify regex filter which will be applied to playlists names. This way you can query any playlists by names.')
@click.option('--audio', '--a', multiple=True,
              help='Get audio files located at the specified local path. You can specify the audio file name as well.')
@click.option('--csv', '--c', multiple=True,
              help='Get tracks from csv playlists located at the specified local path. You can specify the scv file name as well.')
@click.option('--no-recursive', '-r', is_flag=True,
              help='Do not search in subdirectories from the specified path.')
@click.pass_context
def get_tracks(ctx,
               spotify_playlist,
               spotify_entire_library,
               spotify_entire_library_regex,
               audio,
               csv,
               no_recursive,
               ):
    """

Get tracks from sources.

    """

    # if no sources - print help

    # if len(spotify_playlist) == 0 \
    #         and len(spotify_entire_library) == 0 \
    #         and len(spotify_entire_library_regex) == 0 \
    #         and len(audio) == 0 \
    #         and len(csv) == 0:
    #     click.echo('Please, specify the source where to get the tracks from. Execute "spoty get --help" for more info.')
    #     exit()

    all_tags_list = []

    # get csv

    csv_files = []
    tags_list_from_csv = []

    if len(csv) > 0:
        csv_paths = []
        for path in csv:
            if spoty.csv_playlist.is_csv(path):
                if spoty.utils.is_valid_file(path):
                    csv_files.append(path)
            elif spoty.utils.is_valid_path(path):
                csv_paths.append(path)
            else:
                click.echo(f'Cant find path or file: "{path}"', err=True)
                exit()

        file_names = spoty.csv_playlist.find_csvs_in_paths(csv_paths, not no_recursive)
        csv_files.extend(file_names)

        tags_list = spoty.csv_playlist.read_tags_from_csvs(csv_files)
        tags_list_from_csv.extend(tags_list)
        all_tags_list.extend(tags_list)

    audio_files = []
    tags_list_from_audio = []

    # get audio

    if len(audio) > 0:
        audio_paths = []
        for path in audio:
            if spoty.audio_files.is_audio_file(path):
                if spoty.utils.is_valid_file(path):
                    audio_files.append(path)
            elif spoty.utils.is_valid_path(path):
                audio_paths.append(path)
            else:
                click.echo(f'Cant find path or file: "{path}"', err=True)
                exit()

        file_names = spoty.audio_files.find_audio_files_in_paths(audio_paths, not no_recursive)
        audio_files.extend(file_names)

        tags_list = spoty.audio_files.read_audio_files_tags(audio_files)
        tags_list = spoty.utils.add_playlist_index_from_playlist_names(tags_list)
        tags_list_from_audio.extend(tags_list)
        all_tags_list.extend(tags_list)

    spotify_playlists = []
    tags_list_from_spotify = []

    # get spotify

    if len(spotify_playlist) > 0:
        pl = spoty.utils.tuple_to_list(spotify_playlist)
        tracks, tags_list, playlists = spoty.spotify.get_tracks_from_playlists(pl)
        spotify_playlists.extend(playlists)
        tags_list_from_spotify.extend(tags_list)
        all_tags_list.extend(tags_list)

    if len(spotify_entire_library) > 0:
        pl = spoty.utils.tuple_to_list(spotify_entire_library)
        tracks, tags_list, playlists = spoty.spotify.get_tracks_of_spotify_users(pl)
        spotify_playlists.extend(playlists)
        tags_list_from_spotify.extend(tags_list)
        all_tags_list.extend(tags_list)

    if len(spotify_entire_library_regex) > 0:
        for user_and_reg in spotify_entire_library_regex:
            tracks, tags_list, playlists = spoty.spotify.get_tracks_of_spotify_users(user_and_reg[0], user_and_reg[1])
            spotify_playlists.extend(playlists)
            tags_list_from_spotify.extend(tags_list)
            all_tags_list.extend(tags_list)

    # make summary

    summary = []

    if len(tags_list_from_spotify) > 0:
        summary.append(f'{len(tags_list_from_spotify)} tracks found in {len(spotify_playlists)} Spotify playlists.')
    if len(tags_list_from_audio) > 0:
        summary.append(f'{len(tags_list_from_audio)} audio files found in local path.')
    if len(tags_list_from_csv) > 0:
        summary.append(f'{len(tags_list_from_csv)} tracks found in {len(csv_files)} csv playlists.')

    if not (len(tags_list_from_spotify) == len(all_tags_list) or len(tags_list_from_spotify) == 0)\
            or not (len(tags_list_from_audio) == len(all_tags_list) or len(tags_list_from_audio) == 0)\
            or not (len(tags_list_from_csv) == len(all_tags_list)or len(tags_list_from_csv) == 0):
        summary.append(f'Total tracks collected: {len(all_tags_list)}')

    # make context

    context = SpotyContext()
    context.summary = summary
    context.tags_list = all_tags_list

    ctx.obj = context


get_tracks.add_command(filter_group.filter_tracks)

get_tracks.add_command(count_command.count_tracks)
get_tracks.add_command(print_command.print_tracks)
get_tracks.add_command(export_command.export_tracks)
get_tracks.add_command(import_spotify_command.transfer)