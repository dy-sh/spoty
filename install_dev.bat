pip install virtualenv
virtualenv venv
rem venv\scripts\activate

pip install --editable .
dynaconf write toml -p config -s client_id=12345 -s client_secret=QWE

