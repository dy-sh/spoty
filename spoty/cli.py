import spoty.utils
from spoty.commands import local_commands
from spoty.commands import spotify_playlist_commands
from spoty.commands import spotify_like_commands
from spoty.commands import spotify_track_commands
from spoty.commands import get_group
from spoty.commands import deezer_commands
from spoty import plugins_path
import click
import os



class SpotyPluginsCLI(click.MultiCommand):

    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(plugins_path):
            if filename.endswith('.py') and filename != '__init__.py':
                rv.append(filename[:-3].replace('_','-'))
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        ns = {}
        fn = os.path.join(plugins_path, name.replace('-','_') + '.py')
        with open(fn) as f:
            code = compile(f.read(), fn, 'exec')
            eval(code, ns, ns)
        return ns[name.replace('-','_')]

cli2 = SpotyPluginsCLI(help='This tool\'s subcommands are loaded from a plugin folder dynamically.')


@click.group()
def cli():
    """This program allows you to perform various actions with spotify from the console."""
    pass

@cli.command(cls=SpotyPluginsCLI, help='Plugins.')
def plug():
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
        # '--dp','9844466302',
         # '--dgp','%SPOTY_SOURCE% %SPOTY_PLAYLIST_ID% - %SPOTY_PLAYLIST_NAME%',
         # '--sp', '48zAnLhtTz5pvrSy7s2Ca1',
         # '--dp', '2507191384',
         # '--sp', 'https://open.spotify.com/playlist/57VYcWAMIc97Ig41vPpev6',
         '--a', r'.\music\TEST1',
         # '--a', r'.\music\TEST2\qqq',
         # '--c', '.\MUSIC LIBRARY',
         # 'filter', '--leave-duplicates',
         # '--lnt', 'isrc',
         # 'import-spotify',
        'get-second',
        '--a', r'.\music\TEST2',
        # 'compare','--a', r'.\music\TEST2',
        # 'move-duplicates', '--a', r'.\music\TEST2',
        # '-yr',
         # '--gp','pl',
         # 'print',
         # 'export','-a',
         # 'export','-t',
         # 'import-deezer','-ry',
         # 'import-deezer','-ry',
        # 'duplicates','-p',
        'duplicates',
        'move',
        # 'print'
         # '-y',
         ])
