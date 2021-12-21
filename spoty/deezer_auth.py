from deezy.core import *
from flask import Flask, redirect, request
import os
import requests
import webbrowser
import toml
from spoty import settings

DEEZER_APP_ID = settings.default.APP_ID
DEEZER_APP_SECRET = settings.default.APP_SECRET
DEEZER_ACCESS_TOKEN = settings.default.ACCESS_TOKEN
DEEZER_REDIRECT_URI = settings.REDIRECT_URI
arl_file_name = os.path.join(settings.config_path, '.arl')

def do_something():
    print('Server is started')
    webbrowser.open("http://localhost:8888")


class AuthFlaskApp(Flask):
    def run(self, host=None, port=None, debug=None, load_dotenv=True, **options):
        if not self.debug or os.getenv('WERKZEUG_RUN_MAIN') == 'true':
            with self.app_context():
                do_something()
        super(AuthFlaskApp, self).run(host=host, port=port, debug=debug, load_dotenv=load_dotenv, **options)


app = AuthFlaskApp(__name__)


def write_token_to_config_file(token):
    DEEZER_ACCESS_TOKEN = token

    data = toml.load(settings.secrets_file_name)
    data['ACCESS_TOKEN'] = token

    f = open(settings.secrets_file_name, 'w')
    toml.dump(data, f)
    f.close()

    print("Config file updated.")


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


@app.route('/', methods=['GET'])
def default():
    url = (f'https://connect.deezer.com/oauth/auth.php?app_id={DEEZER_APP_ID}'
           f'&redirect_uri={DEEZER_REDIRECT_URI}&perms=manage_library,delete_library,email,offline_access')
    print(url)
    return redirect(url, code=302)


@app.route('/callback', methods=['GET'])
def deezer_login():
    code = request.args.get('code')

    url = (f'https://connect.deezer.com/oauth/access_token.php?app_id={DEEZER_APP_ID}'
           f'&secret={DEEZER_APP_SECRET}&code={code}&output=json')

    response = requests.get(url)

    if response.text == 'wrong code':
        return 'wrong code'

    response = response.json()
    token = response['access_token']
    print("Access token: " + str(token))
    write_token_to_config_file(token)


    shutdown_server()

    return f'<h1>Access token received</h1>{token}<br><br>Now you can use deezy.', {'Content-Type': 'text/html'}


def get_token():
    app.run(host='0.0.0.0', port=8888)


if __name__ == '__main__':
    get_token()
