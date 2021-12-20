import click

import spoty.utils
from spoty.commands import transfer_command
from spoty.commands import local_commands
from spoty.commands import spotify_playlist_commands
from spoty.commands import spotify_like_commands
from spoty.commands import spotify_track_commands


@click.group()
def cli():
    """This program allows you to perform various actions with spotify from the console."""
    pass

cli.add_command(transfer_command.transfer)

cli.add_command(local_commands.local)

@cli.group()
def spotify():
    """Spotify specific commands."""
    pass

spotify.add_command(spotify_playlist_commands.playlist)
spotify.add_command(spotify_like_commands.like)
spotify.add_command(spotify_track_commands.track)



if __name__ == '__main__':
    # cli()
    cli(['transfer',
         # '-P',
         # '--ssu',
         # '--ssu', 'me',
         # '--dgp','%SPOTY_PLAYLIST_SOURCE% %SPOTY_PLAYLIST_ID% - %SPOTY_PLAYLIST_NAME%',
         # '--ssp', '0yRgrCdkntJG83mFbFvrBP',
         # '--ssp', '0yRgrCdkntJG83mFbFvrBP',
         # '--ssp', '0yRgrCdkntJG83mFbFvrBP',
         # '--ssp', 'https://open.spotify.com/playlist/7E6SNhIGjSqEmzHISqnMrJ',
         # 'https://open.spotify.com/playlist/7E6SNhIGjSqEmzHISqnMrJ',
         # r'.\music\Pop Nutral',
         # r'.\music\Techno Nutral',
         # r'.\PLAYLISTS',
         r'.\music',
         # '--fpn', '^BES',
         '-Cda'
         ])
