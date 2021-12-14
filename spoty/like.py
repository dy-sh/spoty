from spoty import sp
from spoty import log
import spoty.utils
import click
import os


def get_liked_tracks_count():
    results = sp.current_user_saved_tracks(limit=50)
    total_likes_count = results['total']
    return total_likes_count


def get_liked_tracks():
    tracks = []

    log.info(f'Collecting liked tracks')

    with click.progressbar(length=100, label='Collecting liked tracks') as bar:
        results = sp.current_user_saved_tracks(limit=50)
        total_likes_count = results['total']
        tracks.extend(results['items'])

        bar.length = total_likes_count
        bar.update(len(tracks))

        log.debug(f'Collected {len(tracks)}/{total_likes_count}')

        while results['next']:
            results = sp.next(results)
            tracks.extend(results['items'])
            bar.update(len(tracks))

            log.debug(f'Collected {len(tracks)}/{total_likes_count}')

    return tracks


def add_tracks_to_liked(track_ids):
    for i in range(len(track_ids)):
        track_ids[i] = spoty.utils.parse_track_id(track_ids[i])

    log.info(f'Adding {len(track_ids)} to saved tracks')

    i = 0
    next_tracks = []
    while i < len(track_ids):
        next_tracks.append(track_ids[i])
        if len(next_tracks) == 50 or i == len(track_ids) - 1:
            sp.current_user_saved_tracks_add(tracks=next_tracks)
            log.debug(f'Added {i + 1}/{len(next_tracks)} tracks to saved')
            next_tracks = []
        i += 1


def export_liked_tracks_to_file(file_name):
    log.info(f'Exporting liked tracks from file "{file_name}"')

    liked_tracks = spoty.like.get_liked_tracks()
    spoty.utils.write_tracks_to_csv_file(liked_tracks, file_name)

    log.success(f'{len(liked_tracks)} liked tracks exported to file: "{file_name}"')

    return liked_tracks


def import_likes_from_file(file_name):
    log.info(f'Importing liked tracks from file "{file_name}"')
    tracks_in_file = spoty.utils.read_tracks_from_csv_file(file_name)
    if len(tracks_in_file) > 0:
        add_tracks_to_liked(tracks_in_file)

    log.success(f'{len(tracks_in_file)} liked tracks imported from file: "{file_name}"')

    return tracks_in_file


def get_likes_for_tracks(track_ids):
    likes = []

    i = 0
    next_tracks = []
    while i < len(track_ids):
        next_tracks.append(track_ids[i])
        if len(next_tracks) == 50 or i == len(track_ids) - 1:
            likes_new = sp.current_user_saved_tracks_contains(tracks=next_tracks)
            likes.extend(likes_new)
            next_tracks = []
        i += 1

    return likes


def get_liked_track_ids(track_ids):
    liked_tracks = []

    likes = get_likes_for_tracks(track_ids)
    for i in range(len(track_ids)):
        if likes[i]:
            liked_tracks.append(track_ids[i])

    return liked_tracks


def get_not_liked_track_ids(track_ids):
    not_liked_tracks = []

    likes = get_likes_for_tracks(track_ids)
    for i in range(len(track_ids)):
        if not likes[i]:
            not_liked_tracks.append(track_ids[i])

    return not_liked_tracks
