spoty
- remove duplicates in playlists by isrc
- search duplicates in all playlists by isrc
- import playlists by isrc or title (import tracks from deezer and local files)
- export playlists for tracks that not exist in local playlists

deezer
- mutithread download
- download only if not exsit in local playlists
- fix logs for russian titles (utf8)

local
- create playlists from local files library
- remove duplicates in local folder by ISRCs (move to folder with "isrc-deezer1.flac" "isrc-spotify1.flac")
- remove existing tracks from folder if exist in another folder by ISRCs
- remove existing tracks from new playlists (generate new playlists without existing)
- read playlists and write spotify_track_id tag from playlist to local files if title matches
- read playlists and write isrc if empty (and check if exist) for local files if title matches

qobuz:
- download tracks
  - https://github.com/KGTasa/chimera
- write isrc

flows:
- sync from local to spotify:
  - create playlists from local files and import them on spotify (reorder sorted, delete bad)
  - delete old spotify playlists
- download new tracks:
  - export new tracks from "=" playlist (optional compare with local playlists),
  - move tracks from "=" playlists to "==" playlists (for downloading it from spotify)
  - import local playlists to deezer
  - download from deezer
  - delete on deezer
