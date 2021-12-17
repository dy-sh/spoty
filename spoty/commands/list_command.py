from spoty import settings
from spoty import log
import spoty.playlist
import spoty.like
import spoty.local
import click
import re
import spoty.utils
import time
import os
from datetime import datetime


@click.command("list")
@click.argument('sources', nargs=-1)
@click.option('--source-spotify-playlist', '--ssp', multiple=True,
              help='Read tracks in specified spotify playlist.')
@click.option('--source-spotify-user', '--ssu', multiple=True,
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
@click.option('--merged-export-filename', '--mef',
              help='Export a list of read tracks to one merged csv playlist with specified name.')
@click.option('--overwrite', '-o', is_flag=True,
              help='Overwrite existing csv playlists without asking')
@click.option('--timestamp', '-t', is_flag=True,
              help='Create a new subfolder with the current date and time for saved csv playlists')
def list(sources,
         source_spotify_playlist,
         source_deezer_playlist,
         source_deezer_user,
         source_spotify_user,
         source_local_files,
         source_local_playlists,
         filter_playlists_names,
         filter_tracks_tags,
         filter_tracks_no_tags,
         no_recursive,
         count,
         print_to_console,
         export_path,
         merged_export_filename,
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

    source_spotify_playlist = to_list(source_spotify_playlist)
    source_spotify_user = to_list(source_spotify_user)
    source_deezer_playlist = to_list(source_deezer_playlist)
    source_deezer_user = to_list(source_deezer_user)
    source_local_files = to_list(source_local_files)
    source_local_playlists = to_list(source_local_playlists)
    filter_playlists_names = to_list(filter_playlists_names)
    filter_tracks_tags = to_list(filter_tracks_tags)
    filter_tracks_no_tags = to_list(filter_tracks_no_tags)

    all_source_tracks_tags = []

    for source in sources:
        if spoty.utils.check_is_playlist_URI(source):
            source_spotify_playlist.append(source)
        elif spoty.local.is_csv(source):
            source_local_playlists.append(source)
        elif spoty.local.is_valid_path(source):
            source_local_files.append(source)
        else:
            click.echo(f'Cant recognize source: "{source}"', err=True)

    source_spotify_tracks = []
    source_spotify_tracks_tags = []

    if len(source_spotify_playlist) > 0:
        playlists = []
        with click.progressbar(source_spotify_playlist, label='Reading spotify playlists') as bar:
            for playlist_id in bar:
                playlist = spoty.playlist.get_playlist(playlist_id)
                playlists.append(playlist)

                if len(filter_playlists_names) > 0:
                    playlists = list(filter(lambda pl: re.findall(filter_playlists_names, pl['name']), playlists))

                tracks = spoty.playlist.get_tracks_of_playlist(playlist_id)

                if len(filter_tracks_tags) > 0:
                    tracks = spoty.utils.filter_spotify_tracks_which_have_all_tags(tracks, filter_tracks_tags)

                if len(filter_tracks_no_tags) > 0:
                    tracks = spoty.utils.filter_spotify_tracks_which_not_have_any_of_tags(tracks, filter_tracks_no_tags)

                tags = spoty.utils.read_tags_from_spotify_tracks(tracks)

                source_spotify_tracks.extend(tracks)
                source_spotify_tracks_tags.extend(tags)
                all_source_tracks_tags.extend(tags)

    source_local_tracks = []
    source_local_tracks_tags = []

    for path in source_local_files:
        path = os.path.abspath(path)
        local_files = spoty.local.get_local_audio_file_names(path, no_recursive)

        if len(filter_tracks_tags) > 0:
            local_files = spoty.local.filter_tracks_which_have_all_tags(local_files, filter_tracks_tags)

        if len(filter_tracks_no_tags) > 0:
            local_files = spoty.local.filter_tracks_which_not_have_any_of_tags(local_files, filter_tracks_no_tags)

        tags=spoty.local.read_tracks_tags(local_files,True)

        source_local_tracks.append(local_files)
        source_local_tracks_tags.extend(tags)
        all_source_tracks_tags.extend(tags)




    # click.echo(f'Local tracks:')
    # for full_file in full_file_names:
    #     click.echo(full_file)

    if count:
        click.echo(f'Total tracks: {len(all_source_tracks_tags)}')

    if print:
        for i, track in enumerate(source_spotify_tracks_tags):
            click.echo(
                f'--------------------- SPOTIFY TRACK {i + 1} / {len(source_spotify_tracks_tags)} ---------------------')
            spoty.utils.print_track_main_tags(track)
        for i, track in enumerate(source_local_tracks_tags):
            click.echo(
                f'--------------------- LOCAL TRACK {i + 1} / {len(source_local_tracks_tags)} ---------------------')
            spoty.utils.print_track_main_tags(track)


def to_list(some_tuple):
    l = []
    l.extend(some_tuple)
    return l
