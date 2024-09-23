import requests
import decrypter
import parser
import yt_dlp
import subprocess
import os


class Tvnz:
    def __init__(self, api_release="public", authorization=None):
        self.API_RELEASE = api_release
        self.BASE_URL = f"https://apis-{self.API_RELEASE}-prod.tech.tvnz.co.nz"
        self.POLICY_KEY = "BCpkADawqM1N12WMDn4W-_kPR1HP17qWAzLwRMnN2S11amDldHxufQMiBfcXaYthGVkx1iJgFCAkbCAJ0R-z8S-gWFcZg7BcmerduckK-Lycyvgpe4prhFDj6jCMrXMq4F5lS5FVEymSDlpMK2-lK87-RK62ifeRgK7m_Q" # Appears to be the same for all requests
        self.authorization = authorization

    def getShow(self, showId):
        # Get the metadata for a video
        videoUrl = f"{self.BASE_URL}/api/v1/web/play/shows/{showId}"
        showMetadata = requests.get(videoUrl).json()

        # Parse the metadata
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
            "categories": [],
            "moods": []
        }

        if showMetadata["portraitTileImage"] != None:
            showInfo['portraitTileImage'] = {
                'url': showMetadata['portraitTileImage']['src'],
                'aspectRatio': showMetadata['portraitTileImage']['aspectRatio']
            }
        else:
            showInfo['portraitTileImage'] = None


        for categories in showMetadata["categories"]:
            showInfo["categories"].append({
                "name": categories["label"],
                "url": categories["href"]
            })

        for mood in showMetadata["moods"]:
            showInfo["moods"].append(mood["label"])

        return showInfo


    def getEpisodes(self, showId, seasonNumber: str=None):
        # Get api endpoints for each season
        showUrl = f"{self.BASE_URL}/api/v1/web/play/shows/{showId}"
        showMetadata = requests.get(showUrl).json()

        seasonList = requests.get(f"{self.BASE_URL}{showMetadata['page']['href']}/episodes").json()["layout"]["slots"]["main"]["modules"][0]["lists"]

        episodes = []
        if seasonNumber is not None:
            for season in seasonList:
                if season["baseHref"].endswith(f"/{seasonNumber}"):
                    seasonData = requests.get(self.BASE_URL + season["baseHref"]).json()
                    episodes.append(parser.parseSeasonData(seasonData))
                    break
        else:
            for season in seasonList:
                seasonData = requests.get(self.BASE_URL + season["baseHref"]).json()
                episodes.append(parser.parseSeasonData(seasonData))

        return episodes


    def getSchedule(self, channelName = None, date = None): # Valid channel names: "TVONE", "TV2", "DUKE", "TVONEPLUS1", "TV2PLUS1", "dukeplus1"
        schedule = {}

        if channelName is not None:
            channelUrls = [f"{self.BASE_URL}/api/v1/web/play/epg/channels/{channelName}/schedule?date={date}"] # date format: yyyy-mm-dd
        else:
            channelUrls = []
            for channel in requests.get(f"{self.BASE_URL}/api/v1/web/play/epg/schedule?date={date}").json()["epgChannels"]:
                channelUrls.append(self.BASE_URL + channel)

        for channel in channelUrls:
            channelSchedule = requests.get(channel).json()
            programLinks = []
            programs = []
            for program in channelSchedule["programmes"]:
                programLinks.append(program)

            for program in programLinks:
                programs.append({
                    "title": channelSchedule["_embedded"][program]["title"],
                    "episodeTitle": channelSchedule["_embedded"][program]["episodeName"],
                    "episodeNumber": channelSchedule["_embedded"][program]["episodeNumber"],
                    "seasonNumber": channelSchedule["_embedded"][program]["seasonNumber"],
                    "description": channelSchedule["_embedded"][program]["synopsis"],
                    "duration": parser.convertDuration(channelSchedule["_embedded"][program]["duration"]),
                    "onTime": channelSchedule["_embedded"][program]["onTime"],
                    "offTime": channelSchedule["_embedded"][program]["offTime"],
                    "rating": channelSchedule["_embedded"][program]["certification"],
                })

                if channelSchedule["_embedded"][program]["showHref"] is not None:
                    programs[-1]["showId"] = channelSchedule["_embedded"][program]["showHref"].split("/")[-1]
                else:
                    programs[-1]["showId"] = None

                schedule[program.split("/")[7]] = programs
        return schedule


    def getVideo(self, videoId):
        # Get the metadata for a video
        videoUrl = f"{self.BASE_URL}/api/v1/web/play/video/{videoId}"
        videoMetadata = requests.get(videoUrl).json()

        # Parse the metadata
        videoInfo = {
            "title": videoMetadata["title"],
            "videoId": videoMetadata["videoId"],
            "description": videoMetadata["synopsis"],
            "url": videoMetadata["page"]["url"],
            "duration": parser.convertDuration(videoMetadata["duration"]),
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
        searchResults = requests.get(f"{self.BASE_URL}/api/v1/web/play/search?q={query}").json()
        results = []
        for result in searchResults["results"]:
            if result["type"] == "show":
                results.append({
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
                    "categories": [],
                    "moods": []
                })

                if result["portraitTileImage"] != None:
                    results[-1]['portraitTileImage'] = {
                        'url': result['portraitTileImage']['src'],
                        'aspectRatio': result['portraitTileImage']['aspectRatio']
                    }
                else:
                    results[-1]['portraitTileImage'] = None

                for categories in result["categories"]:
                    results[-1]["categories"].append({
                        "name": categories["label"],
                        "url": categories["href"]
                    })

                for mood in result["moods"]:
                    results[-1]["moods"].append(mood["label"])


            elif result["type"] == "newsVideo":
                results.append({
                    "title": result["title"],
                    "videoId": result["videoId"],
                    "description": result["description"],
                    "url": result["page"]["url"],
                    "coverImage": result["images"][0]["src"],
                    "onTime": result["onTime"],
                    "offTime": result["offTime"],
                    "videoType": result["videoType"],
                })

                if result["media"] is not None:
                    results[-1]["brightcove"] = {
                        "videoId": result["media"]["id"],
                        "accountId": result["media"]["accountId"]
                    },
                    results[-1]["duration"] = parser.convertDuration(result["media"]["duration"]),
                else:
                    results[-1]["brightcove"] = {
                        "videoId": None,
                        "accountId": None
                    }
                    results[-1]["duration"] = None


            elif result["type"] == "sportVideo":
                results.append({
                    "title": result["title"],
                    "videoId": result["videoId"],
                    "description": result["description"],
                    "url": result["page"]["url"],
                    "coverImage": result["images"][0]["src"],
                    "onTime": result["onTime"],
                    "offTime": result["offTime"],
                    "videoType": result["videoType"],
                })

                if result["media"] is not None:
                    results[-1]["brightcove"] = {
                        "videoId": result["media"]["id"],
                        "accountId": result["media"]["accountId"]
                    },
                    results[-1]["duration"] = parser.convertDuration(result["media"]["duration"]),
                else:
                    results[-1]["brightcove"] = {
                        "videoId": None,
                        "accountId": None
                    }
                    results[-1]["duration"] = None
        return results


    def getCategory(self, categoryName):
        categoryPage = requests.get(f"{self.BASE_URL}/api/v1/web/play/page/categories/{categoryName}").json()
        categoryInfo = {
            "title": categoryPage["title"],
            "description": categoryPage["metadata"]["description"],
            "url": categoryPage["url"],
            "shows": []
        }

        showUrls = []

        for id in categoryPage["layout"]["slots"]["main"]["modules"][0]["items"]:
            showUrls.append(id["href"])

        for show in showUrls:
            categoryInfo["shows"].append({
                "title": categoryPage["_embedded"][show]["title"],
                "showId": categoryPage["_embedded"][show]["showId"],
                "description": categoryPage["_embedded"][show]["synopsis"],
                "url": categoryPage["_embedded"][show]["page"]["url"],
                "episodesAvailable": categoryPage["_embedded"][show]["episodesAvailable"],
                "seasonsAvailable": categoryPage["_embedded"][show]["seasonsAvailable"],
                "coverImage": {
                    "url": categoryPage["_embedded"][show]["coverImage"]["src"],
                    "aspectRatio": categoryPage["_embedded"][show]["coverImage"]["aspectRatio"]
                },
                "tileImage": {
                    "url": categoryPage["_embedded"][show]["tileImage"]["src"],
                    "aspectRatio": categoryPage["_embedded"][show]["tileImage"]["aspectRatio"]
                },
                "rating": categoryPage["_embedded"][show]["rating"]["classification"],
                "isFavorite": categoryPage["_embedded"][show]["preferences"]["isFavorite"],
                "showType": categoryPage["_embedded"][show]["showType"],
                "releaseYear": categoryPage["_embedded"][show]["releaseYear"],
                "categories": [],
                "moods": []
            })

            if categoryPage["_embedded"][show]["portraitTileImage"] != None:
                categoryInfo["shows"][-1]['portraitTileImage'] = {
                    'url': categoryPage['_embedded'][show]['portraitTileImage']['src'],
                    'aspectRatio': categoryPage['_embedded'][show]['portraitTileImage']['aspectRatio']
                }
            else:
                categoryInfo["shows"][-1]['portraitTileImage'] = None

            for categories in categoryPage["_embedded"][show]["categories"]:
                categoryInfo["shows"][-1]["categories"].append({
                    "name": categories["label"],
                    "url": categories["href"]
                })

            for mood in categoryPage["_embedded"][show]["moods"]:
                categoryInfo["shows"][-1]["moods"].append(mood["label"])

        return categoryInfo


    def getAllShowIds(self):
        showList = requests.get(f"{self.BASE_URL}/api/v1/web/play/shows").json()

        showIds = []
        for show in showList:
            showIds.append(show.split("/")[-1])

        return showIds


    def downloadVideo(self, videoId, output):
        # Get data
        videoInfo = self.getVideo(videoId)
        playbackInfoUrl = f"https://playback.brightcovecdn.com/playback/v1/accounts/{videoInfo['brightcove']['accountId']}/videos/{videoInfo['brightcove']['videoId']}"
        playbackInfo = requests.get(playbackInfoUrl, headers={"Accept": f"application/json;pk={self.POLICY_KEY}"}).json()

        # Get urls
        licenseUrl = playbackInfo["sources"][2]["key_systems"]["com.widevine.alpha"]["license_url"]
        mpdUrl = playbackInfo["sources"][2]["src"].replace("http://", "https://")
        decryptionKeys = decrypter.getDecryptionKeys(mpdUrl, licenseUrl)

        #TODO: Fix audio and video downloading (has to be done together)
        #TODO: Figure out how to rename the videos

        # Download video and audio
        videoOptions = {
            'allow_unplayable_formats': True,
            'outtmpl': {
                'default': 'video/video.%(ext)s',
                'chapter': 'video.%(ext)s',
            },
            'quiet': True,
            'no_warnings': True
        }
        videoDownloader = (yt_dlp.YoutubeDL(videoOptions))
        videoDownloader.download([mpdUrl])

        # Rename files
        os.chdir("video")
        files = os.listdir()
        for file in files:
            os.rename(file, "video." + file.split(".")[-1])

        # Decrypt files
        subprocess.run(['mp4decrypt', '--key', decryptionKeys, 'video.m4a', 'audioDec.m4a'], check=True)
        subprocess.run(['mp4decrypt', '--key', decryptionKeys, 'video.mp4', 'videoDec.mp4'], check=True)
        os.chdir("..")

        # Merge audio and video
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', 'video/videoDec.mp4', '-i', 'video/audioDec.m4a', '-c', 'copy', output], check=True)

        # Clean up files
        os.remove("video/video.m4a")
        os.remove("video/video.mp4")
        os.remove("video/videoDec.mp4")
        os.remove("video/audioDec.m4a")

def main():
    api = Tvnz()
    api.downloadVideo("2748497", "final.mp4")

if __name__ == "__main__":
    main()