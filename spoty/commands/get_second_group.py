from spoty.commands.first_list_commands import \
    count_command, \
    delete_command, \
    export_command, \
    import_deezer_command, \
    import_spotify_command, \
    print_command,\
    create_m3u8_command
from spoty.commands.second_list_commands import \
    find_duplicates_second_command
from spoty.commands import filter_second_group
from spoty.commands import get_group
from spoty.commands.duplicates_commands import add_missing_tags_command, move_duplicates_command
from spoty.utils import SpotyContext
import click


@click.group("get")
@click.option('--spotify-playlist', '--sp', multiple=True,
              help='Get tracks from Spotify playlist URI or ID.')
@click.option('--spotify-entire-library', '--s', multiple=True,
              help='Get all tracks from Spotify library (by user URI or ID). To request a list for the current authorized user, use "me" as ID.')
@click.option('--spotify-entire-library-regex', '--sr', nargs=2, multiple=True,
              help='Works the same as --spotify-entire-library, but you can specify regex filter which will be applied to playlists names. This way you can query any playlists by names.')
@click.option('--deezer-playlist', '--dp', multiple=True,
              help='Get tracks from Deezer playlist URI or ID.')
@click.option('--deezer-entire-library', '--d', multiple=True,
              help='Get all tracks from Deezer library (by user URI or ID). To request a list for the current authorized user, use "me" as ID.')
@click.option('--deezer-entire-library-regex', '--dr', nargs=2, multiple=True,
              help='Works the same as --deezer-entire-library, but you can specify regex filter which will be applied to playlists names. This way you can query any playlists by names.')
@click.option('--audio', '--a', multiple=True,
              help='Get audio files located at the specified local path. You can specify the audio file name as well.')
@click.option('--csv', '--c', multiple=True,
              help='Get tracks from csv playlists located at the specified local path. You can specify the scv file name as well.')
@click.option('--no-recursive', '-r', is_flag=True,
              help='Do not search in subdirectories from the specified path.')
@click.pass_obj
def get_second(context: SpotyContext,
            spotify_playlist,
            spotify_entire_library,
            spotify_entire_library_regex,
            deezer_playlist,
            deezer_entire_library,
            deezer_entire_library_regex,
            audio,
            csv,
            no_recursive
            ):
    """
Collect second list of tracks for further actions (see next commands).
    """

    context.summary.append("Collecting second list:")
    get_group.get_tracks_wrapper(context,
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


get_second.add_command(filter_second_group.filter_second)

get_second.add_command(count_command.count_tracks)
get_second.add_command(print_command.print_tracks)
get_second.add_command(export_command.export_tracks)
get_second.add_command(create_m3u8_command.export_tracks)
get_second.add_command(import_spotify_command.import_spotify)
get_second.add_command(import_deezer_command.import_deezer)
get_second.add_command(move_duplicates_command.move_duplicates)
get_second.add_command(delete_command.delete_tracks)
get_second.add_command(add_missing_tags_command.add_missing_tags)
get_second.add_command(find_duplicates_second_command.find_duplicates_second)
