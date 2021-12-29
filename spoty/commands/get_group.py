from spoty.commands.first_list_commands import \
    count_command, \
    delete_command, \
    export_command, \
    import_deezer_command, \
    import_spotify_command, \
    print_command, \
    find_duplicates_command,\
    create_m3u8_command
from spoty.commands import \
    filter_group, \
    get_second_group
from spoty.utils import SpotyContext
import spoty.spotify_api
import spoty.deezer_api
import spoty.audio_files
import spoty.csv_playlist
import spoty.utils
import click


@click.group("get")
@click.option('--spotify-playlist', '--sp', multiple=True,
              help='Get tracks from Spotify playlist URI or ID.')
@click.option('--spotify-entire-library', '--s', multiple=True,
              help='Get all tracks from Spotify library (by user URI or ID). To request a list for the current authorized user, use "me" as ID.')
@click.option('--spotify-entire-library-regex', '--sr', nargs=2, multiple=True,
              help='Works the same as --spotify-entire-library, but you can specify regex filter which will be applied to playlists names. This way you can query any playlists by names. First param - user ID, second param - regex query.')
@click.option('--deezer-playlist', '--dp', multiple=True,
              help='Get tracks from Deezer playlist URI or ID.')
@click.option('--deezer-entire-library', '--d', multiple=True,
              help='Get all tracks from Deezer library (by user URI or ID). To request a list for the current authorized user, use "me" as ID.')
@click.option('--deezer-entire-library-regex', '--dr', nargs=2, multiple=True,
              help='Works the same as --deezer-entire-library, but you can specify regex filter which will be applied to playlists names. This way you can query any playlists by names. First param - user ID, second param - regex query.')
@click.option('--audio', '--a', multiple=True,
              help='Get audio files located at the specified local path. You can specify the audio file name as well.')
@click.option('--csv', '--c', multiple=True,
              help='Get tracks from csv playlists located at the specified local path. You can specify the scv file name as well.')
@click.option('--no-recursive', '-r', is_flag=True,
              help='Do not search in subdirectories from the specified path.')
@click.pass_context
def get_tracks(
        ctx,
        spotify_playlist,
        spotify_entire_library,
        spotify_entire_library_regex,
        deezer_playlist,
        deezer_entire_library,
        deezer_entire_library_regex,
        audio,
        csv,
        no_recursive,
):
    """
Get tracks from sources for further actions (see next commands).
    """

    if ctx.obj is None:
        ctx.obj = SpotyContext()

    ctx.obj.summary.append("Collecting:")

    get_tracks_wrapper(
        ctx.obj,
        spotify_playlist,
        spotify_entire_library,
        spotify_entire_library_regex,
        deezer_playlist,
        deezer_entire_library,
        deezer_entire_library_regex,
        audio,
        csv,
        no_recursive,
    )


def get_tracks_wrapper(
        context: SpotyContext,
        spotify_playlist,
        spotify_entire_library,
        spotify_entire_library_regex,
        deezer_playlist,
        deezer_entire_library,
        deezer_entire_library_regex,
        audio,
        csv,
        no_recursive,
):
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

    # get spotify

    spotify_playlists = []
    tags_list_from_spotify = []

    if len(spotify_playlist) > 0:
        pl = spoty.utils.tuple_to_list(spotify_playlist)
        tracks, tags_list, playlists = spoty.spotify_api.get_tracks_from_playlists(pl)
        spotify_playlists.extend(playlists)
        tags_list_from_spotify.extend(tags_list)
        all_tags_list.extend(tags_list)

    if len(spotify_entire_library) > 0:
        for user_id in spotify_entire_library:
            tracks, tags_list, playlists = spoty.spotify_api.get_tracks_of_spotify_user(user_id)
            spotify_playlists.extend(playlists)
            tags_list_from_spotify.extend(tags_list)
            all_tags_list.extend(tags_list)

    if len(spotify_entire_library_regex) > 0:
        for user_and_reg in spotify_entire_library_regex:
            tracks, tags_list, playlists = spoty.spotify_api.get_tracks_of_spotify_user(user_and_reg[0],
                                                                                        user_and_reg[1])
            spotify_playlists.extend(playlists)
            tags_list_from_spotify.extend(tags_list)
            all_tags_list.extend(tags_list)

    # get deezer

    deezer_playlists = []
    tags_list_from_deezer = []

    if len(deezer_playlist) > 0:
        pl = spoty.utils.tuple_to_list(deezer_playlist)
        tracks, tags_list, playlists = spoty.deezer_api.get_tracks_from_playlists(pl)
        # tags_list = spoty.deezer_api.add_track_release_dates(tags_list)
        deezer_playlists.extend(playlists)
        tags_list_from_deezer.extend(tags_list)
        all_tags_list.extend(tags_list)

    if len(deezer_entire_library) > 0:
        for user_id in deezer_entire_library:
            tracks, tags_list, playlists = spoty.deezer_api.get_tracks_of_deezer_user(user_id)
            deezer_playlists.extend(playlists)
            tags_list_from_deezer.extend(tags_list)
            all_tags_list.extend(tags_list)

    if len(deezer_entire_library_regex) > 0:
        for user_and_reg in deezer_entire_library_regex:
            tracks, tags_list, playlists = spoty.deezer_api.get_tracks_of_deezer_user(user_and_reg[0], user_and_reg[1])
            deezer_playlists.extend(playlists)
            tags_list_from_deezer.extend(tags_list)
            all_tags_list.extend(tags_list)

    # make summary

    summary = []

    if len(tags_list_from_spotify) > 0:
        context.summary.append(f'  {len(tags_list_from_spotify)} tracks found in {len(spotify_playlists)} Spotify playlists.')
    if len(tags_list_from_deezer) > 0:
        context.summary.append(f'  {len(tags_list_from_deezer)} tracks found in {len(deezer_playlists)} Deezer playlists.')
    if len(tags_list_from_audio) > 0:
        context.summary.append(f'  {len(tags_list_from_audio)} audio files found in local path.')
    if len(tags_list_from_csv) > 0:
        context.summary.append(f'  {len(tags_list_from_csv)} tracks found in {len(csv_files)} csv playlists.')

    if not (len(tags_list_from_spotify) == len(all_tags_list) or len(tags_list_from_spotify) == 0) \
            or not (len(tags_list_from_deezer) == len(all_tags_list) or len(tags_list_from_deezer) == 0) \
            or not (len(tags_list_from_audio) == len(all_tags_list) or len(tags_list_from_audio) == 0) \
            or not (len(tags_list_from_csv) == len(all_tags_list) or len(tags_list_from_csv) == 0):
        context.summary.append(f'  {len(all_tags_list)} total tracks collected.')

    if len(all_tags_list) == 0:
        context.summary.append(f'  {len(all_tags_list)} total tracks collected.')

    # make context

    context.tags_lists.append(all_tags_list)


get_tracks.add_command(filter_group.filter_tracks)

get_tracks.add_command(count_command.count_tracks)
get_tracks.add_command(print_command.print_tracks)
get_tracks.add_command(export_command.export_tracks)
get_tracks.add_command(create_m3u8_command.export_tracks)
get_tracks.add_command(import_spotify_command.import_spotify)
get_tracks.add_command(import_deezer_command.import_deezer)
get_tracks.add_command(get_second_group.get_second)
get_tracks.add_command(delete_command.delete_tracks)
get_tracks.add_command(find_duplicates_command.find_duplicates)
