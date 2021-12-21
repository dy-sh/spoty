import click

import spoty.utils
from spoty.commands import local_commands
from spoty.commands import spotify_playlist_commands
from spoty.commands import spotify_like_commands
from spoty.commands import spotify_track_commands
from spoty.commands import get_group


@click.group()
def cli():
    """This program allows you to perform various actions with spotify from the console."""
    pass


cli.add_command(local_commands.local)
cli.add_command(get_group.get_tracks)


@cli.group()
def spotify():
    """Spotify specific commands."""
    pass


spotify.add_command(spotify_playlist_commands.playlist)
spotify.add_command(spotify_like_commands.like)
spotify.add_command(spotify_track_commands.track)

if __name__ == '__main__':
    # cli()
    cli(['get',
         '--sr','me','^BEST',
         # '--s','me',
         # '--dgp','%SPOTY_PLAYLIST_SOURCE% %SPOTY_PLAYLIST_ID% - %SPOTY_PLAYLIST_NAME%',
         # '--sp', '48zAnLhtTz5pvrSy7s2Ca1',
         # '--sp', 'https://open.spotify.com/playlist/57VYcWAMIc97Ig41vPpev6',
         # '--a', r'.\music',
         # '--a', r'C:\Users\Derwish\Documents\Develop\spoty\music\Pop Nutral\24KGoldn - Mood.flac',
         # '--a', '.\music\Techno Nutral',
         # '--c', '.\PLAYLISTS',
         # '--c', '.\PLAYLISTS\Pop Nutral.csv',
         # 'filter', '-l',
         # '--lnt', 'isrc',
         'print',
         ])
