<p align="center">
    <img src="docs/images/icon.png" alt="drawing" width="120" align="center"/>
</p>

<h1 align="center">
Kryptonite
</h1>

<h4 align="center">
Python library for interacting with streaming services to get metadata download media
</h4>

## Features

- Get metadata (title, year, genres, etc.) using official APIs
- Download media (TV shows, episodes, and movies)
- Decrypt Widevine DRM protected content
- Interact with user accounts (login, watchlist, etc.)
- Search for media

## Supported services

Currently, the following services are supported:

- TVNZ+

Future support for the following services is planned:

- ThreeNow

## Installation

1. Clone the repository:

```bash
git clone https://github.com/jacobCrume/Kryptonite
```

2. Install the required packages:

```requirements
google~=3.0.0
protobuf~=5.28.2
pycryptodomex~=3.20.0
requests~=2.32.3
xmltodict~=0.13.0
yt-dlp~=2024.8.6
```

- Python 3.10 or higher
- Valid non-blacklisted CDM module (Widevine L3)
- [ffmpeg](https://www.ffmpeg.org/download.html) (for manipulating media files)
- [bento4](https://www.bento4.com/downloads/) (for decrypting Widevine DRM protected content)

In particular, ffmpeg and bento4 must be in your system's PATH. You can test this by running `ffmpeg` and `mp4decrypt` in your terminal.

3. Install your CDM module (instructions below)

### Obtaining L3 CDM

In order for Kryptonite to download and decrypt Widevine DRM protected content, you must obtain a valid Widevine L3 Content Decryption Module (CDM). [This tutorial](https://www.ismailzai.com/blog/picking-the-widevine-locks) can guide you through getting your hands on one, and also gives a general overview of the process that Kryptonite uses to download and decrypt content. After obtaining the CDM, you must place it in the `Kryptonite/cdm/devices/android_generic` directory.

After placing your CDM files here, your directory should look something like this:

```
android_generic/
├── client_id.bin
├── config.json
├── private_key.pem
└── token.bin
```

## Usage

### Getting Metadata

```python

from kryptonite import kryptonite

# Create a TVNZ object
api = kryptonite.Tvnz()

# Search for shows and movies
searchResults = api.search("Shortland Street")
print(searchResults)

# Get metadata for show or movie
metadata = api.get_show(searchResults[0]["show_id"])
print(metadata)

# Get episodes for show or video ID for movie
episodeList = api.get_episodes(searchResults[0]["show_id"])
print(episodeList)

# Get video metadata
videoMetadata = api.get_video(episodeList[0]["episodes"][0]["video_id"])
print(videoMetadata)
```

### Downloading Media

```python

from kryptonite import kryptonite

# Create a TVNZ object
api = kryptonite.Tvnz()

# Download video with ID "2687673" and save it to "D:/video.mp4"
api.download_video("2687673", "D:/video.mp4")
```

### Downloading Subtitles

```python

from kryptonite import kryptonite

# Create a TVNZ object
api = kryptonite.Tvnz()

# Download subtitles for video with ID "2687673"
subtitles = api.get_subtitles("2687673")
print(subtitles)
```

### Logging In and Getting User Information

```python

from kryptonite import kryptonite

# Create a TVNZ object
api = kryptonite.Tvnz()

# Log in with email and password
api.login("bob@example.com", "password1234")

# Get user data
userData = api.get_user_info()

# Get watchlist
watchlist = api.get_watchlist()

# Add show to watchlist
api.add_to_watchlist("189156")

# Remove show from watchlist
api.remove_from_watchlist("189156")
```

## Why the Name Kryptonite?

Kryptonite is a reference to the way that this project downloads and decrypts Widevine DRM protected content. In the Superman comics, Kryptonite is a mineral from Superman's home planet of Krypton that has the ability to weaken him. In the context of this project, Kryptonite is a tool that can weaken the DRM protection on media files, allowing them to be downloaded and played back without restrictions.

## Credits

- <a href="https://www.freepik.com/icon/gemstone_12741643#fromView=search&page=1&position=70&uuid=77cdad4e-e99a-4e2d-b4a4-d0088461d3bc">Icon by Muhammad Atif</a>
