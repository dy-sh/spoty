import spoty.spotify
import spoty.audio_files
import click
import spoty.utils


@click.group()
def track():
    r"""Playlists management."""
    pass


@track.command("isrc")
@click.argument("isrc")
def track_find_by_isrc(isrc):
    r"""
    Find track by isrc.

    Examples:

        spoty track isrc UK6821402425

    """
    track = spoty.spotify.find_track_by_isrc(isrc)
    if track == None:
        click.echo("Not found")
        return
    tags = spoty.spotify.read_tags_from_spotify_tracks([track])
    spoty.utils.print_main_tags(tags[0])


@track.command("artist-title")
@click.argument("artist")
@click.argument("title")
def track_find_by_title(artist, title):
    r"""
    Find track by artist and title.

    Examples:

        spoty track artist-title "Aaron Static" "When We Love"

    """
    track = spoty.spotify.find_track_by_artist_and_title(artist, title)
    if track == None:
        click.echo("Not found")
        return
    tags = spoty.spotify.read_tags_from_spotify_tracks([track])
    spoty.utils.print_main_tags(tags[0])


@track.command("query")
@click.argument("query")
def tracks_find_by_query(query):
    r"""
    Find tracks by query.

    Examples:

        spoty track query "track: breathe"

    """
    tracks = spoty.spotify.find_track_by_query(query)
    if len(tracks)==0:
        click.echo("Not found")
        return
    tags = spoty.spotify.read_tags_from_spotify_tracks(tracks)
    for t in tags:
        click.echo("------------------------------")
        spoty.utils.print_main_tags(t)