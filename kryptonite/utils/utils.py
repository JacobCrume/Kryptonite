import requests
import shutil
import secrets
import string

def process_show(show_metadata):
    return {
        "title": show_metadata["title"],
        "showId": show_metadata["showId"],
        "description": show_metadata["synopsis"],
        "url": show_metadata["page"]["url"],
        "episodesAvailable": show_metadata["episodesAvailable"],
        "seasonsAvailable": show_metadata["seasonsAvailable"],
        "coverImage": {
            "url": show_metadata["coverImage"]["src"],
            "aspectRatio": show_metadata["coverImage"]["aspectRatio"]
        },
        "tileImage": {
            "url": show_metadata["tileImage"]["src"],
            "aspectRatio": show_metadata["tileImage"]["aspectRatio"]
        },
        "rating": show_metadata["rating"]["classification"],
        "isFavorite": show_metadata["preferences"]["isFavorite"],
        "showType": show_metadata["showType"],
        "releaseYear": show_metadata["releaseYear"],
        "categories": [{"name": cat["label"], "url": cat["href"]} for cat in show_metadata["categories"]],
        "moods": [mood["label"] for mood in show_metadata["moods"]],
        "portraitTileImage": {
            'url': show_metadata['portraitTileImage']['src'],
            'aspectRatio': show_metadata['portraitTileImage']['aspectRatio']
        } if show_metadata["portraitTileImage"] else None
    }
def get_json(url: str, headers=None) -> dict:
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Error fetching data from {url}: {e}")

def generate_nonce(length=32):
    alphabet = string.ascii_letters + string.digits
    nonce = ''.join(secrets.choice(alphabet) for _ in range(length))
    return nonce

def downloadFile(url, output):
    with requests.get(url, stream=True) as r:
        with open(output, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

    return output

def convertDuration(isoDuration):
    # Remove the 'PT' prefix
    isoDuration = isoDuration[2:]

    # Initialize hours, minutes, and seconds
    duration = {"hours": 0, "minutes": 0, "seconds": 0.0}

    # Extract hours, minutes and seconds
    if 'H' in isoDuration:
        hours_part, isoDuration = isoDuration.split('H')
        duration["hours"] = int(hours_part)

    if 'M' in isoDuration:
        minutes_part, isoDuration = isoDuration.split('M')
        duration["minutes"] = int(minutes_part)

    if 'S' in isoDuration:
        duration["seconds"] = float(isoDuration[:-1])

    return duration


def parseSeasonData(seasonData):
    seasonEpisodes = {
        "season_number": seasonData["id"].split("/")[-1],
        "episodes": []
    }
    for episode in seasonData["content"]:
        seasonEpisodes["episodes"].append({
            "title": seasonData["_embedded"][episode["href"]]["title"],
            "episodeNumber": seasonData["_embedded"][episode["href"]]["episodeNumber"],
            "video_id": seasonData["_embedded"][episode["href"]]["video_id"],
            "description": seasonData["_embedded"][episode["href"]]["synopsis"],
            "url": seasonData["_embedded"][episode["href"]]["page"]["url"],
            "coverImage": {
                "url": seasonData["_embedded"][episode["href"]]["image"]["src"],
                "aspectRatio": seasonData["_embedded"][episode["href"]]["image"]["aspectRatio"]
            },
            "onTime": seasonData["_embedded"][episode["href"]]["onTime"],
            "offTime": seasonData["_embedded"][episode["href"]]["offTime"],
            "duration": convertDuration(seasonData["_embedded"][episode["href"]]["duration"]),
            "rating": seasonData["_embedded"][episode["href"]]["certification"],
            "brightcove": {
                "video_id": seasonData["_embedded"][episode["href"]]["publisherMetadata"]["brightcoveVideoId"],
                "accountId": seasonData["_embedded"][episode["href"]]["publisherMetadata"]["brightcoveAccountId"],
                "playerId": seasonData["_embedded"][episode["href"]]["publisherMetadata"]["brightcovePlayerId"]
            }
        })

    if seasonEpisodes["season_number"][:3] == "jcr":
        seasonEpisodes["season_number"] = None
    return seasonEpisodes