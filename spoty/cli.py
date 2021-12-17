import click
from spoty.commands import playlist_commands
from spoty.commands import like_commands
from spoty.commands import local_commands
from spoty.commands import track_commands
from spoty.commands import list_command


@click.group()
def cli():
    """This program allows you to perform various actions with spotify from the console."""
    pass


cli.add_command(playlist_commands.playlist)
cli.add_command(like_commands.like)
cli.add_command(local_commands.local)
cli.add_command(track_commands.track)
cli.add_command(list_command.list)

if __name__ == '__main__':
    # cli()
    cli(['list', '--ssp', '0yRgrCdkntJG83mFbFvrBP', '--ssp',
         'https://open.spotify.com/playlist/7E6SNhIGjSqEmzHISqnMrJ?si=23ae8f6ceb4548b5','-c'])

    # cli(['like', 'count'])
    # cli(['like', 'add','3MH8ie02My2CNzSCH5Pme5', '3L8GYpi8HyhjeixHIlOyM9'])
    # cli(['playlist', 'import-all'])
    # cli(['playlist', 'import-all', "-y", r'C:\Users\Derwish\Documents\Develop\spoty\spoty\MUSIC LIBRARY'])
    # cli(['playlist', 'import', '--append', r'C:\Users\Derwish\Documents\Develop\spotyfy-automation\export\Test playlist.csv'])
    # cli(['playlist', 'export', 'https://open.spotify.com/playlist/4hkN9szbNaxVGmoSa2UHQ5?si=f951fbaa61d842e4'])
    # cli(['playlist', 'export-all', '-yo', "--path", r'C:\Users\Derwish\Documents\Develop\spoty\spoty\MUSIC LIBRARY'])
    # cli(['playlist', 'export-all', "--filter-names", '^='])
    # cli(['playlist', 'export-all', '--timestamp'])
    # cli(['playlist', 'copy', 'https://open.spotify.com/playlist/37i9dQZF1DXe6bgV3TmZOL?si=cb91d11522a643f1'])
    # cli(['playlist', 'copy', '0jnEstbKP0nw8bZs7ilKQo', 'https://open.spotify.com/playlist/2uUxXZ6tmQFG8m0Z7stt4n?si=dd730bb4db90449a', '0jnEstbKP0nw8bZs7ilKQo'])
    # cli(['playlist', 'add-tracks', '0yRgrCdkntJG83mFbFvrBP', '3MH8ie02My2CNzSCH5Pme5', '3L8GYpi8HyhjeixHIlOyM9'])
    # cli(['playlist', 'remove-tracks', '0yRgrCdkntJG83mFbFvrBP', '3MH8ie02My2CNzSCH5Pme5', '3L8GYpi8HyhjeixHIlOyM9'])
    # cli(['playlist', 'remove-liked-tracks', '0yRgrCdkntJG83mFbFvrBP'])
    # cli(['playlist', 'like-all-tracks', '0yRgrCdkntJG83mFbFvrBP'])
    # cli(['local', 'list-tracks', '--have-isrc', '-r',r'C:\Users\Derwish\Documents\Develop\deezy\DOWNLOADS'])
    # cli(['local', 'collect-playlist', "-o", r'C:\Users\Derwish\Documents\Develop\deezy\DOWNLOADS', r"C:\Users\Derwish\Documents\Develop\deezy\DOWNLOADS\EXPORT"])
    # cli(['local', 'collect-playlist', r'C:\Users\Derwish\Music\MusicBee\Music', r"C:\Users\Derwish\Documents\Develop\deezy\DOWNLOADS\EXPORT"])
    # cli(['local', 'collect-playlist', "-o", '--naming-pattern', '%genre% - %mood%', r'C:\Users\Derwish\Music\MusicBee\Music', r"C:\Users\Derwish\Documents\Develop\deezy\DOWNLOADS\EXPORT"])
    # cli(['local', 'count-in-playlists', r"C:\Users\Derwish\Documents\Develop\deezy\DOWNLOADS\EXPORT"])
    # cli(['local', 'count-in-playlists','--have-no-tag', 'title', r"C:\Users\Derwish\Documents\Develop\deezy\DOWNLOADS\EXPORT"])
    # cli(['local', 'list-tracks', '--have-no-tag', 'title,isrc', r"C:\Users\Derwish\Documents\Develop\deezy\DOWNLOADS"])
    # cli(['local', 'list-duplicates-in-playlists', r"C:\Users\Derwish\Documents\Develop\deezy\DOWNLOADS\EXPORT"])
    # cli(['local', 'list-duplicates-in-tracks', '-r','isrc',r"C:\Users\Derwish\Music\MusicBee\Music"])
    # cli(['local', 'list-duplicates-in-tracks', '-r','isrc,isrc',r"C:\Users\Derwish\Music\deemix"])
    # cli(['local', 'add-tags-from-spotify-library', '-r',r'C:\Users\Derwish\Documents\Develop\deezy\DOWNLOADS\test\TEMP',
    #      "--filter-names", r'TEMP', '--user-id','yniwbbotyw3ag2o5s3exexycj'])
    # cli(['local', 'add-tags-from-spotify-library', '-r',r'C:\Users\Derwish\Documents\Develop\deezy\DOWNLOADS\test\2',
    #      "--filter-names", r'^#DL Techno', '--user-id','yniwbbotyw3ag2o5s3exexycj'])
    # cli(['local', 'add-tags-from-tracks', '-r',r'C:\Users\Derwish\Documents\Develop\deezy\DOWNLOADS\test\11',
    #      r'C:\Users\Derwish\Documents\Develop\deezy\DOWNLOADS\test\2'])
    # cli(['local', 'fix-invalid-track-tags', '-r',r'C:\Users\Derwish\Documents\Develop\deezy\DOWNLOADS\test'])
    # cli(['track', 'isrc', 'UK6821402425'])
    # cli(['track', 'artist-title', "Aaron Static", "When We Love"])
    # cli(['track', 'query', "track: breathe"])
