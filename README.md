[Readme in Russian](https://github.com/dy-sh/spoty/blob/master/README-rus.md)

# Spoty

This command line utility allows you to manage the library in music services, as well as work with the tags of the local mp3/flac files.

With this tool you can:
- Manage a music service from the command line - create/copy/delete playlists, search for songs, add them to playlists, like it, etc.
- From the recommendations and playlists of other users, always listen only to the music that you have not yet heard (skip tracks you listened to). New tracks (which you definitely haven't heard yet) will be automatically added to your library from the playlists of other users and recommendations to which you are subscribed.
- Transfer music from one service to another (for example, from Spotify to Deezer), or from one account to another.
- Scan your collection of mp3/flac files and transfer it to a music service.
- Make a backup of your entire music collection from the music service to csv files on disk. Later, you can restore your playlists from these files in any music service. Now you will never lose your library, even if you lose access to your account.
- Clean your library from duplicates (both in music services and in local files).
- Transfer tags from the music service to your local files, or do it between duplicate local audio files.
- Create m3u8 playlists by grouping audio files by specified tags (for example, by style and mood).
- And much more...

Currently, two services are supported - Spotify and Deezer. You can make a request to add the service you need.

The program supports plugins. You can connect the functionality you need, written by the community. The list of plugins will be updated below. 


## How to install

- Install [python](https://www.python.org/downloads/) version 3.7 or higher.
- Install Spoty running the following command in the terminal: 

```batch
pip install spoty
```


## Plugins

Just put the plugin in the plugins folder and it will be connected automatically (for example, `spoty\plugins\collector\collector.py`). 
You can find out the location of the plugins folder by running the `spoty config` command.

- [collector](https://github.com/dy-sh/spoty_collector) - Plugin for collecting music in spotify.
- [tag-cleaner](https://github.com/dy-sh/spoty_tag_cleaner) Plugin for cleaning tags in audio files.
- [genre-from-folder](https://github.com/dy-sh/spoty_genre_from_folder) - The plugin updates Genre and Mood tags in audio files by the name of the parent folder.


## How to setup

The program is ready to use immediately after installation.
The only thing you need to set up is access to your music service. 

### Set up for Spotify

- On the Spotify [applications](https://developer.spotify.com/dashboard/applications) page, click `Create new app`, create a new application. 
- Click `Edit Settings`, in `Redirect URIs` enter `http://localhost:8888/callback`.
- Copy `Client ID` and `Client Secret` into the configuration file `spoty\settings\.secrets.toml` (parameters `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`).
- Run any command for Spotify (for example, `spoty spotify me`) and agree to grant access in the opened browser page.
- Everything is ready. When you run the command `spoty spotify me`, you should see your Spotify username. 

### Set up for Deezer

- Run any command for Deezer (eg `spoty deezer playlist list`), you will be prompted for `ARL`. Open Deezer Web Player in a browser and copy the value of the `arl` cookie, enter it into the console. You can edit this value in the file `spoty\settings\.arl`
- Everything is ready. When you run the command `spoty deezer playlist list`, you should see a list of your playlists. 

## How to use

### Command examples

For any command, you can get detailed help by running the command with the `--help` parameter.
Many commands have huge functionality that can be configured using parameters.
Here are just a few examples, for general introduction to Spoty. 

### Examples with music services

Transfer all playlists from Spotify to Deezer: 

```bash
spoty get --s me import-deezer
```

Transfer all playlists from Deezer to Spotify:

```bash
spoty get --d me import-spotify
```

Move playlists with names starting with "BEST" from Spotify to Deezer (you can use any regex to filter playlists): 

```bash
spoty get --sr me "^BEST" import-deezer
```

Export all playlists of specified Spotify user to csv files on disk: 

```bash
spoty get --s "user-name" export
```

Export specified playlists: 

```bash
spoty get --sp "https://open.spotify.com/playlist/37i9dQZF1DXdEiDkV82etZ" --ps "https://open.spotify.com/playlist/37i9dQZF1DX4uWsCu3SlsH" export
```

Import from csv file to Spotify: 

```bash
spoty get --c "./playlist.csv" import-spotify
```

Remove duplicates in Spotify playlist: 

```bash
spoty get --sp "37i9dQZF1DXdEiDkV82etZ" dup get delete
```

Take all tracks in playlists that contain "my" and delete all tracks that were added before the specified date. 

```bash
spoty get --sr me "my"  --leave-added-before "2022-01-10 08:15:27" delete
```

Take all tracks that were added after the specified date (from all playlists) and copy them into one playlist with the specified name. 

```bash
spoty get --s me --leave-added-after "2022-01-10" import-spotify --grouping-pattern "New tracks"
```

Like all tracks in the playlist: 

```bash
spoty spotify playlist "37i9dQZF1DXdEiDkV82etZ" like-all-tracks
```

Remove all tracks that have a like from the playlist: 

```bash
spoty spotify playlist "37i9dQZF1DXdEiDkV82etZ" remove-liked-tracks
```


Export all liked tracks from Spotify to csv files on disk (you can also import the list): 

```bash
spoty spotify like export
```

Find a track that has the specified title (you can also search by artist, ISRC and other tags): 

```bash
spoty spotify track query "track: breathe"
```


### Examples with local mp3/flac files

Sync local mp3/flac files and Spotify playlists: 

```bash
spoty get --a "./music" sync-spotify
```

Take local files, group them by Genre and Mood, and import these playlists to Spotify:

```bash
spoty get --a "./music" import-spotify --grouping-pattern "%GENRE% %MOOD%"
```

Move duplicates from mp3/flac files to specified folder: 

```bash
spoty get --a "./music" dup get move --p "./duplicates"
```

Take local files from one folder, find their duplicates in another folder, and copy the tags that are missing: 

```bash
spoty get --a "./music1" get --a "./music2" dup add-missing-tags
```

Take local files from one folder, find their duplicates in another folder, and replace the specified tags: 

```bash
spoty get --a "./music1" get --a "./music2" dup replace-tags 'Genre,Mood'
```

Compare audio files in two folders, take only unique files from the first folder and export their list to a csv file: 

```bash
spoty get --a "./music1" get --a "./music2" dup get-unique export 
```

Take audio files, filter out those in which Genre is not specified and make an m3u8 playlist out of them (you can import it into the music player). 

```bash
spoty get --a "./music" filter --leave-no-tags 'Genre' create-m3u8
```


# Development

- Clone repo
- Execute: 
```bash
pip install --editable .
```

Check spoty location:
```bash
spoty config
```

Check spotify connection:
```bash
spoty spotify me
```


