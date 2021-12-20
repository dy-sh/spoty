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


@click.command("transfer")
@click.argument('sources', nargs=-1)
@click.option('--source-spotify-playlist', '--ssp', multiple=True,
              help='Read tracks in specified Spotify playlist (playlist URI or ID).')
@click.option('--source-spotify-user', '--ssu', multiple=True, is_flag=False, flag_value="me",
              help='Read tracks in this Spotify user library (user URI or ID). To request a list for the current user, leave this option empty, or use "me" as ID.')
# @click.option('--source-deezer-playlist', '--sdp', multiple=True,
#               help='Read tracks in specified deezer playlist.')
# @click.option('--source-deezer-user', '--sdu', multiple=True,
#               help='Read tracks in this spotify user library.')
@click.option('--source-audio', '--sa', multiple=True,
              help='Read tracks from audio files located in specified local path.')
@click.option('--source-csv', '--sc', multiple=True,
              help='Read tracks from csv playlists located in specified local path. You can specify the scv filename as well.')
@click.option('--source-no-recursive', '-r', is_flag=True,
              help='Do not search in subdirectories from the specified path.')
@click.option('--filter-playlist-names', '--fpn',
              help='Read only playlists whose names matches this regex filter')
@click.option('--filter-have-tags', '--fht', multiple=True,
              help='Get only tracks that have all of the specified tags.')
@click.option('--filter-have-no-tags', '--fhnt', multiple=True,
              help='Get only tracks that do not have any of the listed tags.')
@click.option('--dest-print', '-P', is_flag=True,
              help='Print a list of read tracks to console.')
@click.option('--dest-csv', '-C', is_flag=True,
              help='Export a list of read tracks to csv playlists on disk.')
@click.option('--dest-spotify', '-S', is_flag=True,
              help='Export a list of read tracks to playlist library.')
@click.option('--dest-option-grouping-pattern', '--dogp', show_default=True,
              default=settings.SPOTY.DEFAULT_DEST_GROUPING_PATTERN,
              help='Exported playlists/files will be named according to this pattern.')
@click.option('--dest-option-duplicates', '-d', type=bool, is_flag=True, default=False,
              help='Allow duplicates (add tracks that are already exist in the playlist).')
@click.option('--dest-option-append', '-a', is_flag=True,
              help='Add tracks to an existing playlist/file if already exists. If this option is not specified, a new playlist/file will always be created.')
@click.option('--dest-option-overwrite', '-o', is_flag=True,
              help='Overwrite existing playlist/file')
@click.option('--dest-option-path', '--dop', show_default=True,
              default=settings.SPOTY.DEFAULT_LIBRARY_PATH,
              help='The path on disk where to export csv playlists.')
@click.option('--dest-option-timestamp', '-t', is_flag=True,
              help='Create a new subfolder with the current date and time for saved csv playlists')
@click.option('--dest-option-print-pattern', '--dopp', show_default=True,
              default=settings.SPOTY.DEFAULT_DEST_PRINT_PATTERN,
              help='Print a list of tracks according to this formatting pattern.')
@click.option('--dest-option-compare-tags', '--sost', show_default=True,
              default=settings.SPOTY.DEFAULT_COMPARE_TAGS,
              help='Compare duplicates by this tags.')
@click.option('--yes-all', '-y', is_flag=True,
              help='Confirm all questions with a positive answer automatically.')
def transfer(sources,
             source_spotify_playlist,
             source_spotify_user,
             # source_deezer_playlist,
             # source_deezer_user,
             source_audio,
             source_csv,
             source_no_recursive,

             filter_playlist_names,
             filter_have_tags,
             filter_have_no_tags,

             dest_print,
             dest_csv,
             dest_spotify,
             dest_option_grouping_pattern,
             dest_option_duplicates,
             dest_option_append,
             dest_option_overwrite,
             dest_option_path,
             dest_option_timestamp,
             dest_option_print_pattern,
             dest_option_compare_tags,
             yes_all,
             ):
    """
Transfer tracks from sources to destination.

You should specify the sources (where to read the tracks) and the destination (where to add/write/print the tracks)

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

\b
Some notes on how to memorize options.
All sources are named with "--source-" and short name "--s" (example: "--source-audio" or "--sa")
All destinations are named with "--dest-" and short name with one capital letter  (example: "--dest-spotify" or "-S")
All single-letter options are switches. They can be combined and do not take any parameter. (example: "-PCo" or -P -C -o)

\b
The option with two dashes (--ssu for example) must be followed by a parameter value.
In some options it is possible not to pass parameter, then the default value will be used.
However, if you leave the parameter blank, you must not pass SOURCE next (otherwise, it will be treated as a parameter).
Examples:
    Correct:
        spoty transfer -P --ssu "me" "./LOCAL_PATH"
        spoty transfer -P "./LOCAL_PATH" --ssu "me"
        spoty transfer -P "./LOCAL_PATH" --ssu
    Wrong:
        spoty transfer -P --ssu "./LOCAL_PATH"
To avoid confusion, better to stick to a simple rule: pass the SOURCES before options.

Many options have default values. You can change them in the config file.

Examples of using:

\b
    Display the number of tracks in the playlists of the current Spotify user:
    spoty transfer --ssu

\b
    Displaying all tracks in the playlists of the current Spotify user:
    spoty transfer --ssu -P

\b
    Export all tracks of the current Spotify user to csv playlists in the default path (overwrite files if they already exist):
    spoty transfer --ssu -Co

\b
    Combination of the two commands above:
    spoty transfer --ssu -PCo

\b
    Displaying all tracks in the playlists whose names start with "BEST":
    spoty transfer -P --ssu --fpn "^BEST"

\b
    Export all tracks of the current Spotify user to csv playlists. Playlists will be named by the names of the playlists in Spotify. You can use any tags for the pattern.
    spoty transfer --ssu -C --enp "%SPOTY_PLAYLIST_NAME%"

\b
    Same as above, but playlists will be named by the artist and album:
    spoty transfer --ssu -C --enp "%ARTIST% - %ALBUM%"

\b
    Display all tracks in two Spotify playlists:
    spoty transfer -P --ssp 37i9dQZF1DX12G1GAEuIuj --ssp 37i9dQZEVXbNG2KDcFcKOF

\b
    Same as above command:
    spoty transfer -P https://open.spotify.com/playlist/37i9dQZF1DX12G1GAEuIuj https://open.spotify.com/playlist/37i9dQZEVXbNG2KDcFcKOF

\b
    Display the number of tracks in Spotify playlist:
    spoty transfer https://open.spotify.com/playlist/37i9dQZF1DX12G1GAEuIuj

\b
    Display all tracks in two local paths:
    spoty transfer -P ./music ./music2

\b
    Display all tracks in local paths. The specified tags will be displayed:
    spoty transfer ./music -P --dpp "%TITLE% - %ARTIST% (%DATE%)"

\b
    Export all tracks from local paths to csv playlist:
    spoty transfer -PC ./music

\b
    Display all tracks in local paths that have the specified tags:
    spoty transfer ./music -P --fht "ISRC" --fht "DATE"

\b
    Display all tracks in local paths that do not have the specified tags:
    spoty transfer ./music -P --fhnt "TITLE"

\b
    Export all tracks from local paths to csv playlist in the specified path:
    spoty transfer -C music --dcp "./music playlists"

\b
    Display all tracks from csv playlists found in path "./PLAYLISTS":
    spoty transfer -P --sc "./PLAYLISTS"

\b
    Display all tracks from csv playlist:
    spoty transfer -P PLAYLISTS/BEST.csv

\b
    Note that if you specify a path as an argument without specifying that it is audio or a playlist (--sa or --sc), then both audio and playlists will be searched in this path:
    spoty transfer -P SOME_FOLDER

\b
    Display all tracks in spotify library with detailed playlist info:
    spoty transfer --ssu -P --dgp "%SPOTY_PLAYLIST_SOURCE% %SPOTY_PLAYLIST_ID% - %SPOTY_PLAYLIST_NAME%"

\b
    Collect playlists from local audio files and import them to Spotify library:
    spoty transfer "./music" -S

\b
    Collect playlists from local audio files, save them to csv files, then read csvs from disk and import tracks to Spotify library:
    spoty transfer --sa "./music" --dop "./EXPORT" -C
    spoty transfer --sc "./EXPORT" -S

\b
    Same as above, but use default path:
    spoty transfer "./music" -C
    spoty transfer "./PLAYLISTS" -S

    """

    # if no sources - print help

    if len(source_spotify_user) == 0 \
            and len(source_spotify_playlist) == 0 \
            and len(source_audio) == 0 \
            and len(source_csv) == 0 \
            and len(sources) == 0:
        transfer(['transfer', '--help'])
        exit()

    # convert tuples to lists

    source_spotify_playlist = to_list(source_spotify_playlist)
    source_spotify_user = to_list(source_spotify_user)
    # source_deezer_playlist = to_list(source_deezer_playlist)
    # source_deezer_user = to_list(source_deezer_user)
    source_audio = to_list(source_audio)
    source_csv = to_list(source_csv)
    filter_have_tags = to_list(filter_have_tags)
    filter_have_no_tags = to_list(filter_have_no_tags)
    dest_option_compare_tags = dest_option_compare_tags.split(',')

    # check input parameters

    if dest_option_append and dest_option_overwrite:
        click.echo(f'Simultaneous use of "--dest-option-append" and "--dest-option-overwrite" is not possible',
                   err=True)
        exit()

    # check sources argument

    source_csv_files = []
    source_csv_paths = []
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
        elif spoty.spotify.check_is_user_URI(source):
            source_spotify_user.append(source)
        elif spoty.csv_playlist.is_csv(source):
            source_csv_files.append(source)
        elif spoty.utils.is_valid_path(source):
            source_audio.append(source)
            source_csv_paths.append(source)
        else:
            click.echo(f'Cant recognize source: "{source}"', err=True)
            exit()

    # read sources

    all_tags = []

    spotify_playlists_tracks, tags_list, spotify_playlists = spoty.spotify.get_tracks_from_spotify_playlists(
        source_spotify_playlist, filter_playlist_names, filter_have_tags, filter_have_no_tags)
    all_tags.extend(tags_list)

    spotify_user_tracks, tags_list, spotify_user_playlists = spoty.spotify.get_tracks_of_spotify_user(
        source_spotify_user, filter_playlist_names, filter_have_tags, filter_have_no_tags)
    all_tags.extend(tags_list)

    audio_file_names = spoty.audio_files.find_audio_files_in_paths(
        source_audio, not source_no_recursive, filter_have_tags, filter_have_no_tags)
    tags_list = spoty.audio_files.read_audio_files_tags(audio_file_names)
    tags_list = spoty.utils.add_playlist_index_from_playlist_names(tags_list)
    all_tags.extend(tags_list)

    csv_file_names = spoty.csv_playlist.find_csvs_in_paths(source_csv_paths, not source_no_recursive)
    csv_file_names.extend(source_csv_files)
    csv_tags_list = spoty.csv_playlist.read_tags_from_csvs(csv_file_names, filter_have_tags, filter_have_no_tags)
    all_tags.extend(csv_tags_list)

    # export to destination

    if dest_print:
        spoty.utils.print_tags_list(all_tags, dest_option_print_pattern, dest_option_grouping_pattern)

    import_to_csv = False
    if dest_csv:
        dest_option_path = os.path.abspath(dest_option_path)

        if dest_option_timestamp:
            now = datetime.now()
            date_time_str = now.strftime("%Y_%m_%d-%H_%M_%S")
            dest_option_path = os.path.join(dest_option_path, date_time_str)

        csv_created_file_names, csv_created_names, csv_added_tracks, csv_import_duplicates, csv_already_exist \
            = spoty.csv_playlist.create_csvs(all_tags, dest_option_path, dest_option_grouping_pattern,
                                             dest_option_overwrite, dest_option_append,
                                             dest_option_duplicates, yes_all, dest_option_compare_tags)

        import_to_csv = True

    import_to_spotify = False
    if dest_spotify:
        click.echo('Next playlists will be imported to Spotify library:')
        grouped_tags = spoty.utils.group_tags_by_pattern(all_tags, dest_option_grouping_pattern)
        for group_name, g_tags_list in grouped_tags.items():
            click.echo(group_name)
        click.echo(f'Total {len(all_tags)} tracks in {len(grouped_tags)} playlists.')

        import_to_spotify = True
        if not yes_all:
            if click.confirm(f'Do you want to continue?'):
                click.echo("")  # for new line
            else:
                click.echo("\nCanceled.")
                import_to_spotify = False
        if import_to_spotify:
            spotify_imported_playlist_ids, spotify_imported_tracks, spotify_import_duplicates, spotify_already_exist, \
            spotify_not_found = spoty.spotify.import_playlists_from_tags_list(
                all_tags, dest_option_grouping_pattern, dest_option_overwrite, dest_option_append,
                dest_option_duplicates, yes_all)

    # print summery

    click.echo('\n-------------------------------------------------------------------------------------')
    print_total = False
    if len(spotify_playlists_tracks) > 0:
        click.echo(f'{len(spotify_playlists_tracks)} tracks found in {len(spotify_playlists)} Spotify playlists.')
        if len(spotify_playlists_tracks) != len(all_tags):
            print_total = True
    if len(spotify_user_tracks) > 0:
        if len(source_spotify_user) == 1:
            click.echo(
                f'{len(spotify_user_tracks)} tracks found in {len(spotify_user_playlists)} playlists in Spotify user library.')
        else:
            click.echo(
                f'{len(spotify_user_tracks)} tracks found in {len(spotify_user_playlists)} playlists in libraries of {len(source_spotify_user)} Spotify users.')
        if len(spotify_user_tracks) != len(all_tags):
            print_total = True
    if len(source_audio) > 0:
        if len(source_audio) == 1:
            click.echo(f'{len(audio_file_names)} audio files found in local path.')
        else:
            click.echo(f'{len(audio_file_names)} audio files found in {len(source_audio)} local paths.')
        if len(audio_file_names) != len(all_tags):
            print_total = True
    if len(csv_tags_list) > 0:
        click.echo(f'{len(csv_tags_list)} tracks found in {len(csv_file_names)} csv playlists.')
        if len(csv_tags_list) != len(all_tags):
            print_total = True
    if print_total:
        click.echo(f'Total tracks found: {len(all_tags)}')

    if import_to_csv:
        mess = f'{len(csv_added_tracks)} tracks written to {len(csv_created_file_names)} csv playlists.'
        if len(csv_import_duplicates) > 0:
            mess += f' {len(csv_import_duplicates)} duplicates in sources skipped.'
        if len(csv_already_exist) > 0:
            mess += f' {len(csv_already_exist)} tracks already exist in csv playlists and skipped.'
        mess += f' Path: "{dest_option_path}"'
        click.echo(mess)

    if import_to_spotify:
        mess = f'{len(spotify_imported_tracks)} tracks imported in {len(spotify_imported_playlist_ids)} Spotify playlists.'
        if len(spotify_import_duplicates) > 0:
            mess += f' {len(spotify_import_duplicates)} duplicates in sources skipped.'
        if len(spotify_already_exist) > 0:
            mess += f' {len(spotify_already_exist)} tracks already exist in playlists and skipped.'
        if len(spotify_not_found) > 0:
            mess += f' {len(spotify_not_found)} tracks not found by tags.'
        click.echo(mess)


def to_list(some_tuple):
    l = []
    l.extend(some_tuple)
    return l
