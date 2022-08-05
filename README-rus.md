[Readme in English](https://github.com/dy-sh/spoty/blob/master/README.md)

# Spoty

Эта консольная утилита позволяет управлять библиотекой в музыкальных сервисах, а так же работать с тэгами локальных mp3/flac файлов.

С помощью этой тулзы вы сможете:
- Управлять музыкальным сервисом из командной строки - создавать/копировать/удалять плейлисты, искать песни, добавлять их в плейлисты, лайкать и т.д.
- Из рекомендаций и плейлистов других пользователей всегда слушать только ту музыку, которую вы еще не слышали, а прослушанные вами треки пропускать. Новые треки, которые вы еще точно не слышали, будут автоматически доабвляться в вашу библитеку из плейлистов других пользоваталей и рекомендаций, на которые вы подписаны.
- Переносить музыку из одного сервиса в другой (к примеру, из Spotify в Deezer), или из одного аккаунта в другой.
- Просканировать свою коллекцию mp3/flac файлов и перенести ее в музыкальный сервис.
- Сделать бэкап всей своей музыкальной коллекции из музыкального сервиса в csv файлы на диске. Позже вы можете восстановить свои плейлисты из этих файлов в любом музыкальном сервисе. Теперь вы никогда не потеряете свою библиотеку, даже если утратите доступ к аккаунту.
- Почистить свою библиотеку от дубликатов (как в музыкальных сервисах, так и в локальных файлах).
- Перенести тэги из музыкального сервиса в ваши локальные файлы, либо сделать это между дубликатами локальных аудио файлов.
- Создавать m3u8 плейлисты, группируя аудио-файлы по заданным тэгам (например, по стилю и настроению).
- И многое другое...

На данный момент поддерживаются два сервиса - Spotify и Deezer. Вы можете сделать запрос на добавление нужного вам сервиса.

Программа поддерживает подключение плагинов. Вы можете подключить нужный вам функционал, написанный комьюнити. Список плагинов будет пополняться ниже.

## Установка

- Установите [python](https://www.python.org/downloads/) не ниже версии 3.7.
- Установите Spoty, выполнив следующую команду в терминале: 

```bash
pip install spoty
```

## Плагины

Чтобы установить плагин, просто положите его в папку с плагинами (например, `spoty\plugins\collector\collector.py`).
Узнать местоположение папки с плагинами можно выполнив команду `spoty config`.

- [collector](https://github.com/dy-sh/spoty_collector) - Plugin for collecting music in spotify.
- [tag-cleaner](https://github.com/dy-sh/spoty_tag_cleaner) Plugin for cleaning tags in audio files.
- [genre-from-folder](https://github.com/dy-sh/spoty_genre_from_folder) - The plugin updates Genre and Mood tags in audio files by the name of the parent folder.

## Как настроить 

Программа готова к использованию сразу после установки. 
Единственное, что вам нужно настроить - доступ к вашему музыкальному сервису.

### Настройка для Spotify

- На странице [applications](https://developer.spotify.com/dashboard/applications) в Spotify нажмите `Create new app`, создайте новое приложение. 
- Нажмите `Edit Settings`, в `Redirect URIs` введите `http://localhost:8888/callback`.
- Скопируйте `Client ID` и `Client Secret` в конфигурационный файл `spoty\settings\.secrets.toml` (параметры `SPOTIFY_CLIENT_ID` и `SPOTIFY_CLIENT_SECRET`).
- Запустите любую команду для Spotify (например `spoty spotify me`) и согласитесь на предоставление доступа в открывшейся странице браузера.
- Все готово. При выполнении команды `spoty spotify me` вы должны увидеть свое имя пользователя в Spotify.

### Настройка для Deezer

- Запустите любую команду для Deezer (например `spoty deezer playlist list`), вам будет предложено ввести `ARL`. Откройте Deezer Web Player в браузере и скопируйте значение куки `arl`, введите его в консоль. Вы можете отредактировать это значение в файле `spoty\settings\.arl` 
- Все готово. При выполнении команды `spoty deezer playlist list` вы должны увидеть список своих плейлистов.

## Как использовать

### Примеры команд

По любой команде вы можете получить подробную справку выполнив команду с параметром `--help`.  
Многие команды имеют огромный функционал, который настраивается с помощью параметров.  
Здесь приведены лишь некоторые примеры, для общего ознакомления с Spoty.  

### Примеры с музыкальными сервисами

Перенести все плейлисты из Spotify в Deezer:

```bash
spoty get --s me import-deezer
```

Перенести все плейлисты из Deezer в Spotify:

```bash
spoty get --d me import-spotify
```

Перенести из Spotify в Deezer плейлисты, имена которых начинаются на "BEST" (вы можете использовать любое регулярное выражение для фильтрации плейлистов):

```bash
spoty get --sr me "^BEST" import-deezer
```

Экспортировать все плейлисты указанного пользователя Spotify в csv файлы на диске:

```bash
spoty get --s "user-name" export
```

Экспортировать указанные плейлисты:

```bash
spoty get --sp "https://open.spotify.com/playlist/37i9dQZF1DXdEiDkV82etZ" --ps "https://open.spotify.com/playlist/37i9dQZF1DX4uWsCu3SlsH" export
```

Импортировать из csv файла в Spotify:

```bash
spoty get --c "./playlist.csv" import-spotify
```

Удалить дубликаты в плейлисте Spotify:

```bash
spoty get --sp "37i9dQZF1DXdEiDkV82etZ" dup get delete
```

Взять все треки в плейлистах, которые содержат "my" и удалить в них все треки, которые были добавлены до указанной даты.

```bash
spoty get --sr me "my"  --leave-added-before "2022-01-10 08:15:27" delete
```

Взять все треки, которые были добавлены после указанной даты (из всех плейлистов), и скопировать в один плейлист с указанным именем.

```bash
spoty get --s me --leave-added-after "2022-01-10" import-spotify --grouping-pattern "New tracks"
```

Лайкнуть все треки в плейлисте:

```bash
spoty spotify playlist "37i9dQZF1DXdEiDkV82etZ" like-all-tracks
```

Удалить все треки, которые имеют лайк из плейлиста:

```bash
spoty spotify playlist "37i9dQZF1DXdEiDkV82etZ" remove-liked-tracks
```


Экспортировать все треки, которым ставили лайк, из Spotify в csv-файлы на диске (так же можно импортировать список):

```bash
spoty spotify like export
```

Найти трек, который имеет указанное название (так же можно искать по исполнителю, ISRC и другим тэгам):

```bash
spoty spotify track query "track: breathe"
```


### Примеры с локальными mp3/flac файлами

Синхронизировать локальные mp3/flac файлы и плейлисты в Spotify:

```bash
spoty get --a "./music" sync-spotify
```

Взять локальные файлы, сгруппировать их по Жанру и Настроению и импортировать такие плейлисты в Spotify:

```bash
spoty get --a "./music" import-spotify --grouping-pattern "%GENRE% %MOOD%"
```

Переместить дубликаты из локальных mp3/flac файлов в указанную папку:

```bash
spoty get --a "./music" dup get move --p "./duplicates"
```

Взять локальные файлы из одной папки, найти их дубликаты в другой папке, и скопировать тэги, которые отсуствуют:

```bash
spoty get --a "./music1" get --a "./music2" dup add-missing-tags
```

Взять локальные файлы из одной папки, найти их дубликаты в другой папке, и заменить указанные тэги:

```bash
spoty get --a "./music1" get --a "./music2" dup replace-tags 'Genre,Mood'
```

Сравнить аудио-файлы в двух папках, взять только уникальные файлы из первой папки и экспортировать их список в csv-файл:

```bash
spoty get --a "./music1" get --a "./music2" dup get-unique export 
```

Взять аудио файлы, отфильтровать те, в которых не указан Жанр и сделать из них плейлист m3u8 (его можно импортировать в музыкальный плеер).

```bash
spoty get --a "./music" filter --leave-no-tags 'Genre' create-m3u8
```


Взять плейлисты из csv-файлов, оставить в них только нужные тэги и экспортировать в новые csv-файлы. 
```bash
spoty get --c "C:\Users\User\Documents\spoty\plugins\collector\cache" export --got 'ARTIST,TITLE'    
```
`
# Development

- Clone repo
- Execute: 
```bash
pip install --editable .
```

Check spoty location:
```bash
spoty config
```

Check spotify connection:
```bash
spoty spotify me
```
