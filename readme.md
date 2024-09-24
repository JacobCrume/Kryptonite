<p align="center"><img src="docs%2Fimages%2Ficon.png" alt="drawing" width="120" align="center"/></p>

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

- Netflix
- Amazon Prime Video
- Disney+

## Installation

Coming soon...

### Requirements

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
- `ffmpeg` (for manipulating media files)
- `bento4` (for decrypting Widevine DRM protected content)

In particular, ffmpeg and bento4 must be in your system's PATH. You can test this by running `ffmpeg` and `mp4decrypt` in your terminal.

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

Coming soon...

## Credits

- <a href="https://www.freepik.com/icon/gemstone_12741643#fromView=search&page=1&position=70&uuid=77cdad4e-e99a-4e2d-b4a4-d0088461d3bc">Icon by Muhammad Atif</a>
