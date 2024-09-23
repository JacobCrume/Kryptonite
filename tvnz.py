import requests
import decrypter
import utils
import yt_dlp
import subprocess
import os


class Tvnz:
    def __init__(self, api_release="public", authorization=None):
        self.API_RELEASE = api_release
        self.BASE_URL = f"https://apis-{self.API_RELEASE}-prod.tech.tvnz.co.nz"
        self.POLICY_KEY = "BCpkADawqM1N12WMDn4W-_kPR1HP17qWAzLwRMnN2S11amDldHxufQMiBfcXaYthGVkx1iJgFCAkbCAJ0R-z8S-gWFcZg7BcmerduckK-Lycyvgpe4prhFDj6jCMrXMq4F5lS5FVEymSDlpMK2-lK87-RK62ifeRgK7m_Q"
        self.authorization = authorization

    def _get_json(self, url, headers=None):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"Error fetching data from {url}: {e}")

    def getShow(self, showId):
        videoUrl = f"{self.BASE_URL}/api/v1/web/play/shows/{showId}"
        showMetadata = self._get_json(videoUrl)

        showInfo = {
            "title": showMetadata["title"],
            "showId": showMetadata["showId"],
            "description": showMetadata["synopsis"],
            "url": showMetadata["page"]["url"],
            "episodesAvailable": showMetadata["episodesAvailable"],
            "seasonsAvailable": showMetadata["seasonsAvailable"],
            "coverImage": {
                "url": showMetadata["coverImage"]["src"],
                "aspectRatio": showMetadata["coverImage"]["aspectRatio"]
            },
            "tileImage": {
                "url": showMetadata["tileImage"]["src"],
                "aspectRatio": showMetadata["tileImage"]["aspectRatio"]
            },
            "rating": showMetadata["rating"]["classification"],
            "isFavorite": showMetadata["preferences"]["isFavorite"],
            "showType": showMetadata["showType"],
            "releaseYear": showMetadata["releaseYear"],
            "categories": [{"name": cat["label"], "url": cat["href"]} for cat in showMetadata["categories"]],
            "moods": [mood["label"] for mood in showMetadata["moods"]],
            "portraitTileImage": {
                'url': showMetadata['portraitTileImage']['src'],
                'aspectRatio': showMetadata['portraitTileImage']['aspectRatio']
            } if showMetadata["portraitTileImage"] else None
        }

        return showInfo

    def getEpisodes(self, showId, seasonNumber=None):
        showUrl = f"{self.BASE_URL}/api/v1/web/play/shows/{showId}"
        showMetadata = self._get_json(showUrl)
        seasonList = self._get_json(f"{self.BASE_URL}{showMetadata['page']['href']}/episodes")["layout"]["slots"]["main"]["modules"][0]["lists"]

        episodes = []
        for season in seasonList:
            if seasonNumber is None or season["baseHref"].endswith(f"/{seasonNumber}"):
                seasonData = self._get_json(self.BASE_URL + season["baseHref"])
                episodes.append(utils.parseSeasonData(seasonData))
                if seasonNumber:
                    break

        return episodes

    def getSchedule(self, channelName=None, date=None):
        schedule = {}
        channelUrls = [f"{self.BASE_URL}/api/v1/web/play/epg/channels/{channelName}/schedule?date={date}"] if channelName else [
            self.BASE_URL + channel for channel in self._get_json(f"{self.BASE_URL}/api/v1/web/play/epg/schedule?date={date}")["epgChannels"]
        ]

        for channel in channelUrls:
            channelSchedule = self._get_json(channel)
            programs = [{
                "title": channelSchedule["_embedded"][program]["title"],
                "episodeTitle": channelSchedule["_embedded"][program]["episodeName"],
                "episodeNumber": channelSchedule["_embedded"][program]["episodeNumber"],
                "seasonNumber": channelSchedule["_embedded"][program]["seasonNumber"],
                "description": channelSchedule["_embedded"][program]["synopsis"],
                "duration": utils.convertDuration(channelSchedule["_embedded"][program]["duration"]),
                "onTime": channelSchedule["_embedded"][program]["onTime"],
                "offTime": channelSchedule["_embedded"][program]["offTime"],
                "rating": channelSchedule["_embedded"][program]["certification"],
                "showId": channelSchedule["_embedded"][program]["showHref"].split("/")[-1] if channelSchedule["_embedded"][program]["showHref"] else None
            } for program in channelSchedule["programmes"]]

            schedule[channel.split("/")[7]] = programs

        return schedule

    def getVideo(self, videoId):
        videoUrl = f"{self.BASE_URL}/api/v1/web/play/video/{videoId}"
        videoMetadata = self._get_json(videoUrl)

        videoInfo = {
            "title": videoMetadata["title"],
            "videoId": videoMetadata["videoId"],
            "description": videoMetadata["synopsis"],
            "url": videoMetadata["page"]["url"],
            "duration": utils.convertDuration(videoMetadata["duration"]),
            "rating": videoMetadata["certification"],
            "coverImage": {
                "url": videoMetadata["image"]["src"],
                "aspectRatio": videoMetadata["image"]["aspectRatio"]
            },
            "videoType": videoMetadata["videoType"],
            "onTime": videoMetadata["onTime"],
            "offTime": videoMetadata["offTime"],
            "showId": videoMetadata["showHref"].split("/")[-1],
            "seasonNumber": videoMetadata["seasonNumber"],
            "episodeNumber": videoMetadata["episodeNumber"],
            "brightcove": {
                "videoId": videoMetadata["publisherMetadata"]["brightcoveVideoId"],
                "accountId": videoMetadata["publisherMetadata"]["brightcoveAccountId"],
                "playerId": videoMetadata["publisherMetadata"]["brightcovePlayerId"]
            }
        }

        return videoInfo

    def search(self, query):
        searchResults = self._get_json(f"{self.BASE_URL}/api/v1/web/play/search?q={query}")
        results = []

        for result in searchResults["results"]:
            if result["type"] == "show":
                show = {
                    "title": result["title"],
                    "showId": result["showId"],
                    "description": result["synopsis"],
                    "url": result["page"]["url"],
                    "episodesAvailable": result["episodesAvailable"],
                    "seasonsAvailable": result["seasonsAvailable"],
                    "coverImage": {
                        "url": result["coverImage"]["src"],
                        "aspectRatio": result["coverImage"]["aspectRatio"]
                    },
                    "tileImage": {
                        "url": result["tileImage"]["src"],
                        "aspectRatio": result["tileImage"]["aspectRatio"]
                    },
                    "rating": result["rating"]["classification"],
                    "releaseYear": result["releaseYear"],
                    "showType": result["showType"],
                    "categories": [{"name": cat["label"], "url": cat["href"]} for cat in result["categories"]],
                    "moods": [mood["label"] for mood in result["moods"]],
                    "portraitTileImage": {
                        'url': result['portraitTileImage']['src'],
                        'aspectRatio': result['portraitTileImage']['aspectRatio']
                    } if result["portraitTileImage"] else None
                }
                results.append(show)
            elif result["type"] in ["sportVideo", "newsVideo"]:
                video = {
                    "title": result["title"],
                    "videoId": result["videoId"],
                    "description": result["description"],
                    "url": result["page"]["url"],
                    "coverImage": result["images"][0]["src"],
                    "onTime": result["onTime"],
                    "offTime": result["offTime"],
                    "videoType": result["videoType"],
                    "brightcove": {
                        "videoId": result["media"]["id"] if result["media"] else None,
                        "accountId": result["media"]["accountId"] if result["media"] else None
                    },
                    "duration": utils.convertDuration(result["media"]["duration"]) if result["media"] else None
                }
                results.append(video)

        return results

    def getCategory(self, categoryName):
        categoryPage = self._get_json(f"{self.BASE_URL}/api/v1/web/play/page/categories/{categoryName}")
        categoryInfo = {
            "title": categoryPage["title"],
            "description": categoryPage["metadata"]["description"],
            "url": categoryPage["url"],
            "shows": []
        }

        for show in categoryPage["layout"]["slots"]["main"]["modules"][0]["items"]:
            showData = categoryPage["_embedded"][show["href"]]
            showInfo = {
                "title": showData["title"],
                "showId": showData["showId"],
                "description": showData["synopsis"],
                "url": showData["page"]["url"],
                "episodesAvailable": showData["episodesAvailable"],
                "seasonsAvailable": showData["seasonsAvailable"],
                "coverImage": {
                    "url": showData["coverImage"]["src"],
                    "aspectRatio": showData["coverImage"]["aspectRatio"]
                },
                "tileImage": {
                    "url": showData["tileImage"]["src"],
                    "aspectRatio": showData["tileImage"]["aspectRatio"]
                },
                "rating": showData["rating"]["classification"],
                "isFavorite": showData["preferences"]["isFavorite"],
                "showType": showData["showType"],
                "releaseYear": showData["releaseYear"],
                "categories": [{"name": cat["label"], "url": cat["href"]} for cat in showData["categories"]],
                "moods": [mood["label"] for mood in showData["moods"]],
                "portraitTileImage": {
                    'url': showData['portraitTileImage']['src'],
                    'aspectRatio': showData['portraitTileImage']['aspectRatio']
                } if showData["portraitTileImage"] else None
            }
            categoryInfo["shows"].append(showInfo)

        return categoryInfo

    def getAllShowIds(self):
        showList = self._get_json(f"{self.BASE_URL}/api/v1/web/play/shows")
        return [show.split("/")[-1] for show in showList]

    def downloadVideo(self, videoId, output):
        videoInfo = self.getVideo(videoId)
        playbackInfoUrl = f"https://playback.brightcovecdn.com/playback/v1/accounts/{videoInfo['brightcove']['accountId']}/videos/{videoInfo['brightcove']['videoId']}"
        playbackInfo = self._get_json(playbackInfoUrl, headers={"Accept": f"application/json;pk={self.POLICY_KEY}"})

        licenseUrl = playbackInfo["sources"][2]["key_systems"]["com.widevine.alpha"]["license_url"]
        mpdUrl = playbackInfo["sources"][2]["src"].replace("http://", "https://")
        decryptionKeys = decrypter.getDecryptionKeys(mpdUrl, licenseUrl)

        videoOptions = {
            'allow_unplayable_formats': True,
            'outtmpl': 'video/video.%(ext)s',
            'quiet': True,
            'no_warnings': True
        }
        videoDownloader = yt_dlp.YoutubeDL(videoOptions)
        videoDownloader.download([mpdUrl])

        os.chdir("video")
        for file in os.listdir():
            os.rename(file, "video." + file.split(".")[-1])

        subprocess.run(['mp4decrypt', '--key', decryptionKeys, 'video.m4a', 'audioDec.m4a'], check=True)
        subprocess.run(['mp4decrypt', '--key', decryptionKeys, 'video.mp4', 'videoDec.mp4'], check=True)
        os.chdir("..")

        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', 'video/videoDec.mp4', '-i', 'video/audioDec.m4a', '-c', 'copy', output], check=True)

        os.remove("video/video.m4a")
        os.remove("video/video.mp4")
        os.remove("video/videoDec.mp4")
        os.remove("video/audioDec.m4a")

    def getSubtitles(self, videoId):
        videoInfo = self.getVideo(videoId)
        playbackInfoUrl = f"https://playback.brightcovecdn.com/playback/v1/accounts/{videoInfo['brightcove']['accountId']}/videos/{videoInfo['brightcove']['videoId']}"
        playbackInfo = self._get_json(playbackInfoUrl, headers={"Accept": f"application/json;pk={self.POLICY_KEY}"})

        subtitlesUrl = playbackInfo["text_tracks"][0]["sources"][1]["src"]
        return requests.get(subtitlesUrl).content

    def login(self):
        # Authentication request
        auth = requests.post("https://login.tvnz.co.nz/co/authenticate", headers={
            "Origin": "https://login.tech.tvnz.co.nz",
            "Referer": "https://login.tech.tvnz.co.nz"
        }, data={
            "client_id": "LnDAd4mARcCg8VnOhNmr22el46J91FmS",
            "credential_type": "password",
            "password": input("Password: "),
            "username": input("Username: "),
        })

        authentication = auth.json()

        # Access token request
        access_token = requests.get("https://login.tvnz.co.nz/authorize", params={
            "client_id": "LnDAd4mARcCg8VnOhNmr22el46J91FmS",
            "response_type": "token id_token",
            "audience": "tvnz-apis",
            "connection": "tvnz-users",
            "redirect_uri": "https://login.tech.tvnz.co.nz/callback/login",
            "state": utils.generate_nonce(),
            "nonce": utils.generate_nonce(),
            "login_ticket": authentication["login_ticket"],
            "scope": "openid profile email",
            "auth0Client": "eyJuYW1lIjoiYXV0aDAuanMiLCJ2ZXJzaW9uIjoiOS4xMS4zIn0="
        }, cookies=auth.cookies, allow_redirects=True)

        self.authorization = access_token.url.split("access_token=")[1]

        return self.authorization

def main():
    api = Tvnz()
    print(api.getSchedule("TVONE", "2024-09-23"))


if __name__ == "__main__":
    main()