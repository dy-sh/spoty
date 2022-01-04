import spoty.spotify_api
import spoty.audio_files
import click
import spoty.utils


@click.group()
def track():
    r"""Playlists management."""
    pass


@track.command("id")
@click.argument("id")
def track_find_by_id(id):
    r"""
    Find track by ID.
    """
    track = spoty.spotify_api.find_track_by_id(id)
    if track == None:
        click.echo("Not found")
        return
    tags = spoty.spotify_api.read_tags_from_spotify_tracks([track])
    spoty.utils.print_main_tags(tags[0])


@track.command("isrc")
@click.argument("isrc")
def track_find_by_isrc(isrc):
    r"""
    Find track by ISRC.

    Examples:

        spoty spotify track ISRC UK6821402425

    """
    tracks = spoty.spotify_api.find_track_by_isrc(isrc)
    if tracks == None:
        click.echo("Not found")
        return
    for i, track in enumerate(tracks):
        tags = spoty.spotify_api.read_tags_from_spotify_track(track)
        print(f"----------------- {i+1}\{len(tracks)} -------------------")
        spoty.utils.print_main_tags(tags)


@track.command("artist-title")
@click.argument("artist")
@click.argument("title")
def track_find_by_title(artist, title):
    r"""
    Find track by artist and title.

    Examples:

        spoty spotify track artist-title "Aaron Static" "When We Love"

    """
    tracks = spoty.spotify_api.find_track_by_artist_and_title(artist, title)
    if tracks == None:
        click.echo("Not found")
        return
    for i, track in enumerate(tracks):
        tags = spoty.spotify_api.read_tags_from_spotify_track(track)
        print(f"----------------- {i+1}\{len(tracks)} -------------------")
        spoty.utils.print_main_tags(tags)


@track.command("query")
@click.argument("query")
def tracks_find_by_query(query):
    r"""
    Find tracks by query.

    Examples:

        spoty spotify track query "track: breathe"

    """
    tracks = spoty.spotify_api.find_track_by_query(query)
    if tracks == None:
        click.echo("Not found")
        return
    for i, track in enumerate(tracks):
        tags = spoty.spotify_api.read_tags_from_spotify_track(track)
        print(f"----------------- {i+1}\{len(tracks)} -------------------")
        spoty.utils.print_main_tags(tags)
