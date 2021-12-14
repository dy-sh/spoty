from spoty import sp
from spoty import log
import spoty.utils
import click


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


def add_tracks(track_ids):
    track_ids = list(track_ids)

    for i in range(len(track_ids)):
        track_ids[i] = spoty.utils.parse_track_id(track_ids[i])

    log.info(f'Adding {len(track_ids)} to saved tracks')

    i = 0
    next_tracks = []
    while i < len(track_ids):
        next_tracks.append(track_ids[i])
        if len(next_tracks) == 50 or i == len(track_ids) - 1:
            sp.current_user_saved_tracks_add(tracks=next_tracks)
            log.debug(f'Added {i+1}/{len(next_tracks)} tracks to saved')
            next_tracks = []
        i += 1



