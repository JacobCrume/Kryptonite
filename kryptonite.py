import requests
from utils import decrypter, utils
import yt_dlp
import subprocess
import os
import shutil
from utils.decorators import requires_login


class Tvnz:
    """
    A class to interact with the TVNZ API

    ...

    Attributes
    ----------
    API_RELEASE : str
        the release of the TVNZ API to use, can be either "public" or "edge"
    BASE_URL : str
        the base url for the TVNZ API
    POLICY_KEY : str
        the policy key for the TVNZ API
    authorization : str
        the authorization token for the TVNZ API

    Methods
    -------
    getShow(showId: str) -> dict
        Gets the metadata for a show or movie with the given ID
    getEpisodes(showId: str, seasonNumber: int = None) -> list
        Gets the episodes for a show with the given ID
    getSchedule(channelName: str=None, date: str=None) -> dict
        Gets the schedule for a given channel on a given date
    getVideo(videoId: str) -> dict
        Gets the metadata for a video with the given ID
    search(query: str) -> list
        Searches the TVNZ API for shows and videos matching the given query
    getCategory(categoryName: str) -> dict
        Gets the shows and movies in a category with the given name
    getAllShowIds() -> list
        Gets a list of all show and movie IDs
    downloadVideo(videoId: str, output: str) -> int
        Downloads a video with the given ID to the given output directory
    getSubtitles(videoId: str) -> str
        Gets the subtitles for a video with the given ID
    login() -> str
        Logs into the TVNZ API and returns the authorization token
    """
    def __init__(self, api_release="public", authorization=None):
        self.API_RELEASE = api_release
        self.BASE_URL = f"https://apis-{self.API_RELEASE}-prod.tech.tvnz.co.nz"
        self.POLICY_KEY = "BCpkADawqM1N12WMDn4W-_kPR1HP17qWAzLwRMnN2S11amDldHxufQMiBfcXaYthGVkx1iJgFCAkbCAJ0R-z8S-gWFcZg7BcmerduckK-Lycyvgpe4prhFDj6jCMrXMq4F5lS5FVEymSDlpMK2-lK87-RK62ifeRgK7m_Q"
        self.authorization = authorization
        self.activeProfile = None
        self.session = requests.Session()

    def getShow(self, showId: str) -> dict:
        """
        Gets the metadata for a show or movie with the given ID

        Parameters:
            showId (str): The ID of the show or movie to get the metadata for

        Returns:
            dict: The metadata for the show or movie with the given ID
        """
        videoUrl = f"{self.BASE_URL}/api/v1/web/play/shows/{showId}"
        showMetadata = utils.get_json(videoUrl)

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

    def getEpisodes(self, showId: str, seasonNumber: int = None) -> list:
        """
        Gets the episodes for a show with the given ID

        Parameters:
            showId (str): The ID of the show to get the episodes for
            seasonNumber (int): The season number to get the episodes for, or None to get all episodes

        Returns:
            list: A list of episodes for the show with the given ID
        """
        showUrl = f"{self.BASE_URL}/api/v1/web/play/shows/{showId}"
        showMetadata = utils.get_json(showUrl)

        episodes = []

        if showMetadata["showType"] == "Episodic":
            # Get a list of seasons from TVNZ api
            seasonList = utils.get_json(f"{self.BASE_URL}{showMetadata['page']['href']}/episodes")["layout"]["slots"]["main"]["modules"][0]["lists"]

            # Iterate through each season, adding its episodes to the last
            for season in seasonList:
                # Check if season number matches the one requested, or, if none was requested, get all the seasons
                if seasonNumber is None or season["baseHref"].endswith(f"/{seasonNumber}"):
                    # Get the metadata for the season and add it to the episode list
                    seasonData = utils.get_json(self.BASE_URL + season["baseHref"])
                    episodes.append(utils.parseSeasonData(seasonData))
                    # If a season number was requested, break the loop
                    if seasonNumber:
                        break

        elif showMetadata["showType"] == "Movie":
            videoInfo = self.getVideo(showMetadata["watchAction"]["videoHref"].split("/")[-1])
            episodes.append({
                "seasonNumber": "1",
                "episodes": [videoInfo]
            })

        return episodes

    def getSchedule(self, channelName: str=None, date: str=None) -> dict:
        """
        Gets the schedule for a given channel on a given date

        Parameters:
            channelName (str): The name of the channel to get the schedule for, or None to get the schedule for all channels
            date (str): The date to get the schedule for in the format "YYYY-MM-DD"

        Returns:
            dict: The schedule for the given channel on the given date
        """
        schedule = {}
        # If a channel name is provided, get the schedule for that channel, otherwise get the schedule for all channels
        channelUrls = [f"{self.BASE_URL}/api/v1/web/play/epg/channels/{channelName}/schedule?date={date}"] if channelName else [
            self.BASE_URL + channel for channel in utils.get_json(f"{self.BASE_URL}/api/v1/web/play/epg/schedule?date={date}")["epgChannels"]
        ]

        for channel in channelUrls:
            channelSchedule = utils.get_json(channel)
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

    def getVideo(self, videoId: str) -> dict:
        """
        Gets the metadata for a video with the given ID

        Parameters:
            videoId (str): The ID of the video to get the metadata for

        Returns:
            dict: The metadata for the video with the given ID
        """
        videoUrl = f"{self.BASE_URL}/api/v1/web/play/video/{videoId}"
        videoMetadata = utils.get_json(videoUrl)

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

    def search(self, query: str) -> list:
        """
        Searches the TVNZ API for shows and movies matching the given query

        Parameters:
            query (str): The query to search for

        Returns:
            list: A list of shows and movies matching the given query
        """
        searchResults = utils.get_json(f"{self.BASE_URL}/api/v1/web/play/search?q={query}")
        results = []

        for result in searchResults["results"]:
            # Check if the result is a show or movie, as they have different metadata
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
            # Check if the result is a sports or new video, as they have different metadata
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

    def getCategory(self, categoryName: str) -> dict:
        """
        Gets the shows and movies in a category with the given name

        Parameters:
            categoryName (str): The name of the category to get the shows and movies for

        Returns:
            dict: The shows and movies in the category with the given name
        """
        categoryPage = utils.get_json(f"{self.BASE_URL}/api/v1/web/play/page/categories/{categoryName}")
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

    def getAllShowIds(self) -> list:
        """
        Gets a list of all show and movie IDs

        Returns:
            list: A list of all show and movie IDs
        """
        showList = utils.get_json(f"{self.BASE_URL}/api/v1/web/play/shows")
        return [show.split("/")[-1] for show in showList]

    def downloadVideo(self, videoId: str, output: str) -> int:
        """
        Downloads a video with the given ID to the given output directory

        Parameters:
            videoId (str): The ID of the video to download
            output (str): The name and directory to save the video to (e.g. "D:/Downloads/video.mp4")

        Returns:
            int: 0 if the video was downloaded successfully, 1 if there was an error
        """

        # TODO: Implement a fully python-based solution for decrypting and combining the files

        # Get video info, specifically as the video's brightcove id and account id
        videoInfo = self.getVideo(videoId)
        playbackInfoUrl = f"https://playback.brightcovecdn.com/playback/v1/accounts/{videoInfo['brightcove']['accountId']}/videos/{videoInfo['brightcove']['videoId']}"
        playbackInfo = utils.get_json(playbackInfoUrl, headers={"Accept": f"application/json;pk={self.POLICY_KEY}"})

        # Get the decryption keys for the video
        licenseUrl = playbackInfo["sources"][2]["key_systems"]["com.widevine.alpha"]["license_url"]
        mpdUrl = playbackInfo["sources"][2]["src"].replace("http://", "https://")
        decryptionKeys = decrypter.getDecryptionKeys(mpdUrl, licenseUrl)

        # Download the video and audio files
        videoOptions = {
            'allow_unplayable_formats': True,
            'outtmpl': 'video/video.%(ext)s',
            'quiet': True,
            'no_warnings': True
        }
        videoDownloader = yt_dlp.YoutubeDL(videoOptions)
        videoDownloader.download([mpdUrl])

        # Rename the video files to remove the random text in the filename
        os.chdir("video")
        for file in os.listdir():
            os.rename(file, "video." + file.split(".")[-1])

        # Decrypt the video and audio files
        subprocess.run(['mp4decrypt', '--key', decryptionKeys, 'video.m4a', 'audioDec.m4a'], check=True)
        subprocess.run(['mp4decrypt', '--key', decryptionKeys, 'video.mp4', 'videoDec.mp4'], check=True)
        os.chdir("..")

        # Combine the video and audio files
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', 'video/videoDec.mp4', '-i',
                        'video/audioDec.m4a', '-c', 'copy', 'video/final.mp4'], check=True)

        # Clean up the files
        os.remove("video/video.m4a")
        os.remove("video/video.mp4")
        os.remove("video/videoDec.mp4")
        os.remove("video/audioDec.m4a")

        # Move the final video to the output directory
        shutil.move("video/final.mp4", output)

        # Check if the file was downloaded successfully
        if os.path.exists(output):
            return 0
        else:
            return 1

    def getSubtitles(self, videoId: str) -> str:
        """
        Gets the subtitles for a video with the given ID

        Parameters:
            videoId (str): The ID of the video to get the subtitles for

        Returns:
            str: The subtitles for the video with the given ID
        """
        videoInfo = self.getVideo(videoId)
        playbackInfoUrl = f"https://playback.brightcovecdn.com/playback/v1/accounts/{videoInfo['brightcove']['accountId']}/videos/{videoInfo['brightcove']['videoId']}"
        playbackInfo = utils.get_json(playbackInfoUrl, headers={"Accept": f"application/json;pk={self.POLICY_KEY}"})

        # Get the subtitles url and download the subtitles
        subtitlesUrl = playbackInfo["text_tracks"][0]["sources"][1]["src"]
        return self.session.get(subtitlesUrl).text

    def login(self, email: str, password: str) -> str:
        """
        Logs into the TVNZ API and returns the authorization token

        Parameters:
            email (str): The email to log in with
            password (str): The password to log in with

        Returns:
            str: The authorization token for the TVNZ API
        """
        # Authentication request
        auth = self.session.post("https://login.tvnz.co.nz/co/authenticate", headers={
            "Origin": "https://login.tech.tvnz.co.nz",
            "Referer": "https://login.tech.tvnz.co.nz"
        }, data={
            "client_id": "LnDAd4mARcCg8VnOhNmr22el46J91FmS",
            "credential_type": "password",
            "password": password,
            "username": email,
        })

        authentication = auth.json()

        # Access token request
        access_token = self.session.get("https://login.tvnz.co.nz/authorize", params={
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

        self.authorization = access_token.url.split("access_token=")[1].split("&")[0]

        return self.authorization

    @requires_login
    def getUserInfo(self) -> list:
        """
        Gets the profile information for the logged-in user

        Returns:
            dict: The profile information for the logged-in user
        """
        profileData = utils.get_json(f"{self.BASE_URL}/api/v1/web/consumer/account", headers={"Authorization": f"Bearer {self.authorization}"})

        profiles = []

        for profile in profileData["profiles"]:
            profiles.append({
                "profileId": profile["id"],
                "accountId": profile["accountId"],
                "firstName": profile["firstName"],
                "lastName": profile["lastName"],
                "verified": True if profile["verificationState"] == "verified" else False,
                "profileType": profile["profileType"],
                "contentRestriction": profile["contentRestriction"],
                "yearOfBirth": profile["yearOfBirth"],
                "gender": profile["gender"],
                "IconImage": {
                    "url": profile["iconImage"]["src"],
                    "aspectRatio": profile["iconImage"]["aspectRatio"]
                },
                "accountOwner": profile["accountOwner"],
                "email": profile["email"],
            })

        return profiles

    @requires_login
    def getProfileIcons(self) -> list:
        """
        Gets the profile icons available

        Returns:
            list: The profile icons available for use
        """
        profileData = utils.get_json(f"{self.BASE_URL}/api/v1/web/consumer/profile-icons", headers={"Authorization": f"Bearer {self.authorization}"})

        icons = []

        for icon in profileData["icons"]:
            icons.append({
                "url": icon["iconImage"]["src"],
                "aspectRatio": icon["iconImage"]["aspectRatio"]
            })

        return icons

    @requires_login
    def setActiveProfile(self, profileId: str) -> str:
        """
        Sets the active profile for the logged-in user

        Returns:
            str: The active profile ID
        """
        self.activeProfile = profileId
        return self.activeProfile

    @requires_login
    def getWatchedVideos(self) -> list:
        """
        Gets the videos the logged-in user has watched and the duration watched

        Returns:
            list: The videos the logged-in user has watched and the duration watched
        """

        watchedData = utils.get_json(f"https://apis-public-prod.tvnz.io/user/v1/play-state", headers={
            "Authorization": f"Bearer {self.authorization}",
            "x-tvnz-active-profile-id": self.activeProfile
        })

        watchedVideos = []

        for video in watchedData["videos"]:
            watchedVideos.append({
                "videoId": video["videoId"],
                "durationWatched": utils.convertDuration(video["duration"])
            })

        return watchedVideos

    @requires_login
    def getWatchList(self) -> list:
        """
        Gets the videos the logged-in user has added to their watchlist

        Returns:
            list: The videos the logged-in user has added to their watchlist
        """
        watchListData = utils.get_json(f"{self.BASE_URL}/api/v1/web/play/page/categories/my-list", headers={
            "Authorization": f"Bearer {self.authorization}",
            "x-tvnz-active-profile-id": self.activeProfile
        })

        watchListShows = []

        for show in watchListData["layout"]["slots"]["main"]["modules"][0]["items"]:
            showData = watchListData["_embedded"][show["href"]]
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
            watchListShows.append(showInfo)

        return watchListShows

    @requires_login
    def addToWatchList(self, showId: str) -> str:
        """
        Adds a show or movie to the logged-in user's watchlist

        Parameters:
            showId (str): The ID of the show or movie to add to the watchlist

        Returns:
            str: The ID of the show or movie added to the watchlist
        """
        response = self.session.post(f"{self.BASE_URL}/api/v1/web/play/shows/{showId}/preferences", headers={
            "Authorization": f"Bearer {self.authorization}",
            "x-tvnz-active-profile-id": self.activeProfile
        }, json={"isFavorite": True})

        if response.status_code == 200:
            return showId

    @requires_login
    def removeFromWatchList(self, showId: str) -> str:
        """
        Removes a show or movie from the logged-in user's watchlist

        Parameters:
            showId (str): The ID of the show or movie to remove from the watchlist

        Returns:
            str: The ID of the show or movie removed from the watchlist
        """
        response = self.session.post(f"{self.BASE_URL}/api/v1/web/play/shows/{showId}/preferences", headers={
            "Authorization": f"Bearer {self.authorization}",
            "x-tvnz-active-profile-id": self.activeProfile
        }, json={"isFavorite": False})

        if response.status_code == 200:
            return showId


def main():
    api = Tvnz()
    api.login(input("Email: "), input("Password: "))
    api.setActiveProfile(api.getUserInfo()[0]["profileId"])
    print(api.removeFromWatchList("190870"))


if __name__ == "__main__":
    main()