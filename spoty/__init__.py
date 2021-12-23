import os

from dynaconf import Dynaconf
from loguru import logger as log


log.remove() # remove default handler to prevent printing to console
log.add('logs/logs.log', level='DEBUG', encoding="utf8")

current_directory = os.path.dirname(os.path.realpath(__file__))
config_path = os.path.abspath(os.path.join(current_directory, '..', 'config'))
settings_file_name = os.path.join(config_path, 'settings.toml')
secrets_file_name = os.path.join(config_path, '.secrets.toml')
plugins_path = os.path.join(os.path.dirname(__file__), '../plugins')

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

