import spoty.local
import os


def get_tracks_from_local_path(source_paths, no_recursive, filter_tracks_tags, filter_tracks_no_tags):
    local_file_names = []
    local_tags = []

    for path in source_paths:
        path = os.path.abspath(path)
        local_files = spoty.local.get_local_audio_file_names(path, no_recursive)

        if len(filter_tracks_tags) > 0:
            local_files = spoty.local.filter_tracks_which_have_all_tags(local_files, filter_tracks_tags)

        if len(filter_tracks_no_tags) > 0:
            local_files = spoty.local.filter_tracks_which_not_have_any_of_tags(local_files, filter_tracks_no_tags)

        tags = spoty.local.read_local_audio_tracks_tags(local_files, True)

        local_file_names.append(local_files)
        local_tags.extend(tags)

    return local_file_names, local_tags
