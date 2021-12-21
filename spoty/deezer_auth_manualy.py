from spoty import settings
import spoty
from deezersdk.deezersdk import Deezer
from spoty import settings
import os

DEEZER_APP_ID = settings.default.DEEZER_APP_ID
DEEZER_APP_SECRET = settings.default.DEEZER_APP_SECRET
DEEZER_ACCESS_TOKEN = settings.default.DEEZER_ACCESS_TOKEN
DEEZER_REDIRECT_URI = settings.DEEZER.REDIRECT_URI
arl_file_name = os.path.join(spoty.config_path, '.arl')


def get_token():
    url = Deezer.get_oauth_login_url(
        app_id=DEEZER_APP_ID,
        redirect_uri=DEEZER_REDIRECT_URI
    )

    print("Open this url in browser and copy code from url (...callback?code=).")
    print(url)

    print("Enter code here:")

    code = input()

    token = Deezer.get_oauth_token(app_id=DEEZER_APP_ID, app_secret=DEEZER_APP_SECRET, code=code)

    print("Access token:")
    print(token)



