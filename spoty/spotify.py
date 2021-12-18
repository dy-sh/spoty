import spoty.utils
import spoty.playlist
import click
import re

def get_tracks_from_spotify_playlists(source_spotify_playlists, filter_playlists_names, filter_tracks_tags,
                                      filter_tracks_no_tags):
    spotify_tracks = []
    source_tags = []

    if len(source_spotify_playlists) > 0:
        playlists = []
        with click.progressbar(source_spotify_playlists, label='Reading spotify playlists') as bar:
            for playlist_id in bar:
                playlist = spoty.playlist.get_playlist(playlist_id)
                playlists.append(playlist)

        if len(filter_playlists_names) > 0:
            playlists = list(filter(lambda pl: re.findall(filter_playlists_names, pl['name']), playlists))

        with click.progressbar(playlists, label='Reading spotify tracks') as bar:
            for playlist in bar:

                tracks = spoty.playlist.get_tracks_of_playlist(playlist['id'])
                for track in tracks:
                    track['track']['SPOTY_PLAYLIST_NAME'] = playlist['name']

                if len(filter_tracks_tags) > 0:
                    tracks = spoty.utils.filter_spotify_tracks_which_have_all_tags(tracks, filter_tracks_tags)

                if len(filter_tracks_no_tags) > 0:
                    tracks = spoty.utils.filter_spotify_tracks_which_not_have_any_of_tags(tracks, filter_tracks_no_tags)

                tags = spoty.utils.read_tags_from_spotify_tracks(tracks)

                spotify_tracks.extend(tracks)
                source_tags.extend(tags)

    return spotify_tracks, source_tags


