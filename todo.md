spoty
- remove duplicates in playlists by isrc
- search duplicates in all playlists by isrc
- export playlists for tracks that not exist in local playlists

deezer
- mutithread download
- download only if not exsit in local playlists
- fix logs for russian titles (utf8)
- fix continue downloading, delete last file

local
CHANGE LOGGER!!!!
- remove duplicates in local folder
- remove duplicates in local folder from folder if exist in another folder
- remove existing tracks from new playlists (generate new playlists without existing)


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
