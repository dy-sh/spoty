import spoty.utils
from spoty import settings_file_name, secrets_file_name, plugins_path
from spoty.commands import spotify_playlist_commands
from spoty.commands import spotify_like_commands
from spoty.commands import spotify_track_commands
from spoty.commands import get_group
from spoty.commands import deezer_commands
from spoty import spotify_api
from spoty import plugins_path
import click
import os


class SpotyPluginsCLI(click.MultiCommand):

    def list_commands(self, ctx):
        rv = []
        for dir in os.listdir(plugins_path):
            plugin_dir=os.path.abspath(os.path.join(plugins_path,dir))
            if os.path.isdir(plugin_dir):
                filename = os.path.join(plugin_dir,dir+'.py')
                if os.path.isfile(filename):
                    rv.append(dir.replace('_', '-'))
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        ns = {}
        fn = os.path.join(plugins_path, name.replace('-', '_'), name.replace('-', '_') + '.py')

        if not os.path.isfile(fn):
            click.echo(
                f'Plugin "{name}" not installed. Execute "spoty plug" command to see a list of installed plugins.',
                err=True)
            exit()

        with open(fn) as f:
            code = compile(f.read(), fn, 'exec')
            eval(code, ns, ns)
        return ns[name.replace('-', '_')]



@click.group()
def cli():
    """This program allows you to perform various actions with spotify from the console."""
    pass


@cli.command("config")
def config():
    """
Prints configuration parameters.
    """
    click.echo(f'Settings file name: {settings_file_name}')
    click.echo(f'Secrets file name: {secrets_file_name}')
    click.echo(f'Plugins path: {plugins_path}')

@cli.command(cls=SpotyPluginsCLI, help='Plugins.')
def plug():
    pass


cli.add_command(get_group.get_tracks)
cli.add_command(deezer_commands.deezer)


@cli.group()
def spotify():
    """Spotify specific commands."""
    pass


@spotify.command("me")
def spotify_me():
    """Print current user name."""
    me = spotify_api.get_sp().me()
    click.echo(f'Current user: "{me["display_name"]}" ({me["id"]})')


spotify.add_command(spotify_playlist_commands.playlist)
spotify.add_command(spotify_like_commands.like)
spotify.add_command(spotify_track_commands.track)

if __name__ == '__main__':
    cli([
        # 'get','export','--help',
    ])
