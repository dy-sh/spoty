import click

import spoty.utils
from spoty.commands import local_commands
from spoty.commands import spotify_playlist_commands
from spoty.commands import spotify_like_commands
from spoty.commands import spotify_track_commands
from spoty.commands import get_group
from spoty.commands import deezer_commands


@click.group()
def cli():
    """This program allows you to perform various actions with spotify from the console."""
    pass


cli.add_command(local_commands.local)
cli.add_command(get_group.get_tracks)
cli.add_command(deezer_commands.deezer)


@cli.group()
def spotify():
    """Spotify specific commands."""
    pass


spotify.add_command(spotify_playlist_commands.playlist)
spotify.add_command(spotify_like_commands.like)
spotify.add_command(spotify_track_commands.track)

if __name__ == '__main__':
    # cli()
    cli([
        # 'deezer','playlist','list'
        'get',
         # '--sr','me','^BEST',
         # '--dr','me','^BEST',
         # '--d','me',
         # '--dgp','%SPOTY_PLAYLIST_SOURCE% %SPOTY_PLAYLIST_ID% - %SPOTY_PLAYLIST_NAME%',
         # '--sp', '48zAnLhtTz5pvrSy7s2Ca1',
         # '--dp', '9809325662',
         # '--sp', 'https://open.spotify.com/playlist/57VYcWAMIc97Ig41vPpev6',
         '--a', r'.\music\TEST1',
         # '--a', r'.\music\Pop Nutral\24KGoldn - Mood.flac',
         # '--a', '.\music\Techno Nutral',
         # '--c', '.\MUSIC LIBRARY',
         # '--c', '.\PLAYLISTS\Pop Nutral.csv',
         # 'filter', '-l',
         # '--lnt', 'isrc',
         # 'import-spotify',
         'compare',
        '--a', r'.\music\TEST2',
        # '-yr',
         # '--gp','pl',
         # 'print',
         # 'export',
         ])
