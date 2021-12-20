import spotipy
import os
from spotipy.oauth2 import SpotifyOAuth
from dynaconf import Dynaconf
from loguru import logger as log

log.remove() # remove default handler to prevent printing to console
log.add('logs/logs.log', level='DEBUG')

current_directory = os.path.dirname(os.path.realpath(__file__))
settings_file_name = os.path.abspath(os.path.join(current_directory, '..', 'config', 'settings.toml'))
secrets_file_name = os.path.abspath(os.path.join(current_directory, '..', 'config', '.secrets.toml'))

if not os.path.isfile(settings_file_name):
    print(f'No config file found at path: {settings_file_name}')
    exit()

if not os.path.isfile(secrets_file_name):
    print(f'No config file found at path: {secrets_file_name}')
    exit()

settings = Dynaconf(
    envvar_prefix="SPOTY",
    settings_files=[settings_file_name, secrets_file_name],
)

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(settings.default.SPOTIFY_CLIENT_ID,
                                               settings.default.SPOTIFY_CLIENT_SECRET,
                                               settings.SPOTIFY.REDIRECT_URI,
                                               scope="user-library-read user-library-modify playlist-modify-private playlist-read-private playlist-modify-public"))


