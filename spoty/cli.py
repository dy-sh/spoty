import click
from spoty.commands import playlist_commands
from spoty.commands import like_commands
from spoty.commands import local_commands


@click.group()
def cli():
    """This program allows you to perform various actions with spotify from the console."""
    pass




cli.add_command(playlist_commands.playlist)
cli.add_command(like_commands.like)
cli.add_command(local_commands.local)


if __name__ == '__main__':
    # cli()
    # cli(['like', 'count'])
    # cli(['like', 'add','3MH8ie02My2CNzSCH5Pme5', '3L8GYpi8HyhjeixHIlOyM9'])
    # cli(['playlist', 'import-all'])
    # cli(['playlist', 'import-all', r'C:\Users\Derwish\Documents\Develop\spotyfy-automation\! MY MUSIC LIBRARY'])
    # cli(['playlist', 'import', '--append', r'C:\Users\Derwish\Documents\Develop\spotyfy-automation\export\Test playlist.csv'])
    # cli(['playlist', 'export-all', "--path", 'C:\\Users\\Derwish\\Downloads\\test'])
    # cli(['playlist', 'export-all', "--filter-names", '^='])
    # cli(['playlist', 'export-all', '--timestamp'])
    # cli(['playlist', 'copy', 'https://open.spotify.com/playlist/37i9dQZF1DXe6bgV3TmZOL?si=cb91d11522a643f1'])
    # cli(['playlist', 'copy', '0jnEstbKP0nw8bZs7ilKQo', 'https://open.spotify.com/playlist/2uUxXZ6tmQFG8m0Z7stt4n?si=dd730bb4db90449a', '0jnEstbKP0nw8bZs7ilKQo'])
    # cli(['playlist', 'add-tracks', '0yRgrCdkntJG83mFbFvrBP', '3MH8ie02My2CNzSCH5Pme5', '3L8GYpi8HyhjeixHIlOyM9'])
    # cli(['playlist', 'remove-tracks', '0yRgrCdkntJG83mFbFvrBP', '3MH8ie02My2CNzSCH5Pme5', '3L8GYpi8HyhjeixHIlOyM9'])
    # cli(['playlist', 'remove-liked-tracks', '0yRgrCdkntJG83mFbFvrBP'])
    # cli(['playlist', 'like-all-tracks', '0yRgrCdkntJG83mFbFvrBP'])
    # cli(['local', 'list', '--have-isrc', '-r',r'C:\Users\Derwish\Documents\Develop\deezy\DOWNLOADS'])
    # cli(['local', 'export-all', "-o", r'C:\Users\Derwish\Documents\Develop\deezy\DOWNLOADS', r"C:\Users\Derwish\Documents\Develop\deezy\DOWNLOADS\EXPORT"])
    cli(['local', 'export-all', "-o", r'C:\Users\Derwish\Music\MusicBee\Music', r"C:\Users\Derwish\Documents\Develop\deezy\DOWNLOADS\EXPORT"])
