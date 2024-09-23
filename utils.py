import requests
import shutil
import secrets
import string

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
        "seasonNumber": seasonData["id"].split("/")[-1],
        "episodes": []
    }
    for episode in seasonData["content"]:
        seasonEpisodes["episodes"].append({
            "title": seasonData["_embedded"][episode["href"]]["title"],
            "episodeNumber": seasonData["_embedded"][episode["href"]]["episodeNumber"],
            "videoId": seasonData["_embedded"][episode["href"]]["videoId"],
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
                "videoId": seasonData["_embedded"][episode["href"]]["publisherMetadata"]["brightcoveVideoId"],
                "accountId": seasonData["_embedded"][episode["href"]]["publisherMetadata"]["brightcoveAccountId"],
                "playerId": seasonData["_embedded"][episode["href"]]["publisherMetadata"]["brightcovePlayerId"]
            }
        })

    if seasonEpisodes["seasonNumber"][:3] == "jcr":
        seasonEpisodes["seasonNumber"] = None
    return seasonEpisodes