from spoty import sp
from spoty import log
import spoty.local
import spoty.utils
import spoty.like
import os.path
import click
import time
import re


def find_track_by_query(query):
    res = sp.search(query)

    try:
        # todo: find for the best matching by album, length and other tags
        tracks = res['tracks']['items']
        return tracks
    except:
        pass

    return []

def find_track_by_isrc(isrc):
    res = sp.search(f'isrc:{isrc}')

    try:
        # todo: find for the best matching by album, length and other tags
        track = res['tracks']['items'][0]
        return track
    except:
        pass

    return None


def find_track_id_by_isrc(isrc):
    track = find_track_by_isrc(isrc)
    return track['id'] if track is not None else None


def find_track_by_artist_and_title(artist, title):
    res = sp.search(f'track:{title} artist:{artist}')

    try:
        # todo: find for the best matching by album, length and other tags
        track = res['tracks']['items'][0]
        return track
    except:
        pass

    return None


def find_track_id_by_artist_and_title(artist, title):
    track = find_track_by_artist_and_title(artist, title)
    return track['id'] if track is not None else None


def find_tracks_from_tags(tag_tracks):
    found_ids = []
    not_found_tracks = []
    for tag_track in tag_tracks:
        if "SPOTIFY_TRACK_ID" in tag_track:
            found_ids.append(tag_track['SPOTIFY_TRACK_ID'])
            continue

        if "ISRC" in tag_track:
            id = find_track_id_by_isrc(tag_track['ISRC'])
            if id is not None:
                found_ids.append(id)
            continue

        if "TITLE" in tag_track and "ARTIST" in tag_track:
            id = find_track_id_by_artist_and_title(tag_track['ARTIST'], tag_track['TITLE'])
            if id is not None:
                found_ids.append(id)
            continue

        not_found_tracks += tag_track

    return found_ids
