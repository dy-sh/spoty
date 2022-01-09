# Spoty

This command line utility allows you to manage the library in music services, as well as work with the tags of the local mp3/flac files.

With this tool you can:
- Manage a music service from the command line - create / copy / delete playlists, search for songs, add them to playlists, like it, etc.
- From the recommendations and playlists of other users, always listen only to the music that you have not yet heard (skip tracks you listened to). New tracks (which you definitely haven't heard yet) will be automatically added to your library from the playlists of other users and recommendations to which you are subscribed.
- Transfer music from one service to another (for example, from Spotify to Deezer), or from one account to another.
- Scan your collection of mp3 / flac files and transfer it to a music service.
- Make a backup of your entire music collection from the music service to csv files on disk. Later, you can restore your playlists from these files in any music service. Now you will never lose your library, even if you lose access to your account.
- Clean your library from duplicates (both in music services and in local files).
- Transfer tags from the music service to your local files, or do it between duplicate local audio files.
- Create m3u8 playlists by grouping audio files by specified tags (for example, by style and mood).
- And much more...

Currently, two services are supported - Spotify and Deezer. You can make a request to add the service you need.

The program supports plugins. You can connect the functionality you need, written by the community. The list of plugins will be updated below. 


## Plugins

Just put the plugin in the plugins folder and it will be connected automatically. 

- [collector](https://github.com/dy-sh/spoty_collector) - Plugin for collecting music in spotify.
- [tag-cleaner](https://github.com/dy-sh/spoty_tag_cleaner) Plugin for cleaning tags in audio files.
- [genre-from-folder](https://github.com/dy-sh/spoty_genre_from_folder) - The plugin updates Genre and Mood tags in audio files by the name of the parent folder.

