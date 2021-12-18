import click
import spoty.utils
import os


def export_tags(all_tags, export_path, export_naming_pattern, overwrite):
    exported_playlists_file_names = []
    exported_playlists_names = []
    exported_tracks = []

    if len(all_tags) > 0:
        grouped_tracks = spoty.utils.group_tracks_by_pattern(export_naming_pattern, all_tags)

        for group, tracks in grouped_tracks.items():
            playlist_name = group
            playlist_name = spoty.utils.slugify_file_pah(playlist_name)
            playlist_file_name = os.path.join(export_path, playlist_name + '.csv')

            if playlist_file_name in exported_playlists_file_names:
                spoty.local.write_tracks_to_csv_file(tracks, playlist_file_name, True)
            else:
                if os.path.isfile(playlist_file_name) and not overwrite:
                    if not click.confirm(f'File "{playlist_file_name}" already exist. Overwrite?'):
                        continue

                spoty.local.write_tracks_to_csv_file(tracks, playlist_file_name, False)

            exported_playlists_names.append(playlist_name)
            exported_playlists_file_names.append(playlist_file_name)
            exported_tracks.extend(tracks)

        mess = f'\n{len(exported_tracks)} tracks exported to {len(exported_playlists_file_names)} playlists in path: "{export_path}"'
        click.echo(mess)

    return exported_playlists_file_names, exported_playlists_names, exported_tracks