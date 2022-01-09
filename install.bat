pip install virtualenv
virtualenv venv
rem venv\scripts\activate

pip install .
dynaconf write toml -p config -s SPOTIFY_CLIENT_ID="" -s SPOTIFY_CLIENT_SECRET="" -s DEEZER_APP_ID=0 -s DEEZER_APP_SECRET="" -s DEEZER_ACCESS_TOKEN=""
