import requests
from .utils import decrypter, utils
import yt_dlp
import subprocess
import os
import shutil
from .utils.decorators import requires_login
from requests.exceptions import RequestException
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    getShow(show_id: str) -> dict
        Gets the metadata for a show or movie with the given ID
    getEpisodes(show_id: str, season_number: int = None) -> list
        Gets the episodes for a show with the given ID
    getSchedule(channel_name: str=None, date: str=None) -> dict
        Gets the schedule for a given channel on a given date
    getVideo(video_id: str) -> dict
        Gets the metadata for a video with the given ID
    search(query: str) -> list
        Searches the TVNZ API for shows and videos matching the given query
    getCategory(category_name: str) -> dict
        Gets the shows and movies in a category with the given name
    getAllShowIds() -> list
        Gets a list of all show and movie IDs
    downloadVideo(video_id: str, output: str) -> int
        Downloads a video with the given ID to the given output directory
    getSubtitles(video_id: str) -> str
        Gets the subtitles for a video with the given ID
    login() -> str
        Logs into the TVNZ API and returns the authorization token
    """

    def __init__(self, api_release="public", authorization=None):
        self.API_RELEASE = api_release
        self.BASE_URL = f"https://apis-{self.API_RELEASE}-prod.tech.tvnz.co.nz"
        self.POLICY_KEY = ("BCpkADawqM1N12WMDn4W-_kPR1HP17qWAzLwRMnN2S11amDldHxufQMiBfcXaYthGVkx1iJgFCAkbCAJ0R-z8S"
                           "-gWFcZg7BcmerduckK-Lycyvgpe4prhFDj6jCMrXMq4F5lS5FVEymSDlpMK2-lK87-RK62ifeRgK7m_Q")
        self.authorization = authorization
        self.activeProfile = None
        self.session = requests.Session()

    def get_show(self, show_id: str) -> dict:
        """
        Gets the metadata for a show or movie with the given ID

        Parameters:
            show_id (str): The ID of the show or movie to get the metadata for

        Returns:
            dict: The metadata for the show or movie with the given ID
        """
        video_url = f"{self.BASE_URL}/api/v1/web/play/shows/{show_id}"
        try:
            logger.info(f"Fetching show metadata for show {show_id}")
            show_metadata = utils.get_json(video_url)
        except RequestException as e:
            logger.error(f"Failed to fetch show metadata: {e}")
            return {}
        logger.info(f"Show metadata received for show {show_id}")
        return utils.process_show(show_metadata)

    def get_episodes(self, show_id: str, season_number: int = None) -> list:
        """
        Gets the episodes for a show with the given ID

        Parameters:
            show_id (str): The ID of the show to get the episodes for
            season_number (int): The season number to get the episodes for, or None to get all episodes

        Returns:
            list: A list of episodes for the show with the given ID
        """
        show_url = f"{self.BASE_URL}/api/v1/web/play/shows/{show_id}"
        logger.info(f"Fetching show metadata for show {show_id}")
        show_metadata = utils.get_json(show_url)
        logger.info(f"Show metadata received for show {show_id}")

        episodes = []

        logger.info(f"Extracting episodes for show {show_id}")
        if show_metadata["showType"] == "Episodic":
            # Get a list of seasons from TVNZ api
            season_list = \
                utils.get_json(f"{self.BASE_URL}{show_metadata['page']['href']}/episodes")["layout"]["slots"]["main"][
                    "modules"][0]["lists"]

            # Iterate through each season, adding its episodes to the last
            for season in season_list:
                # Check if season number matches the one requested, or, if none was requested, get all the seasons
                if season_number is None or season["baseHref"].endswith(f"/{season_number}"):
                    # Get the metadata for the season and add it to the episode list
                    season_data = utils.get_json(self.BASE_URL + season["baseHref"])
                    episodes.append(utils.parseSeasonData(season_data))
                    # If a season number was requested, break the loop
                    if season_number:
                        break

        elif show_metadata["showType"] == "Movie":
            video_info = self.get_video(show_metadata["watchAction"]["videoHref"].split("/")[-1])
            episodes.append({
                "seasonNumber": "1",
                "episodes": [video_info]
            })

        logger.info(f"Episodes extracted for show {show_id}")
        return episodes

    def get_schedule(self, channel_name: str = None, date: str = None) -> dict:
        """
        Gets the schedule for a given channel on a given date

        Parameters: channel_name (str): The name of the channel to get the schedule for, or None to get the schedule
        for all channels date (str): The date to get the schedule for in the format "YYYY-MM-DD"

        Returns:
            dict: The schedule for the given channel on the given date
        """
        schedule = {}
        # If a channel name is provided, get the schedule for that channel, otherwise get the schedule for all channels
        logger.info(f"Fetching schedule for channel {channel_name} on date {date}")
        channel_urls = [
            f"{self.BASE_URL}/api/v1/web/play/epg/channels/{channel_name}/schedule?date={date}"] if channel_name else [
            self.BASE_URL + channel for channel in
            utils.get_json(f"{self.BASE_URL}/api/v1/web/play/epg/schedule?date={date}")["epgChannels"]
        ]
        logger.info(f"Schedule received for channel {channel_name} on date {date}")

        logger.info(f"Extracting schedule for channel {channel_name} on date {date}")
        for channel in channel_urls:
            channel_schedule = utils.get_json(channel)
            programs = [{
                "title": channel_schedule["_embedded"][program]["title"],
                "episodeTitle": channel_schedule["_embedded"][program]["episodeName"],
                "episodeNumber": channel_schedule["_embedded"][program]["episodeNumber"],
                "seasonNumber": channel_schedule["_embedded"][program]["seasonNumber"],
                "description": channel_schedule["_embedded"][program]["synopsis"],
                "duration": utils.convertDuration(channel_schedule["_embedded"][program]["duration"]),
                "onTime": channel_schedule["_embedded"][program]["onTime"],
                "offTime": channel_schedule["_embedded"][program]["offTime"],
                "rating": channel_schedule["_embedded"][program]["certification"],
                "showId": channel_schedule["_embedded"][program]["showHref"].split("/")[-1] if
                channel_schedule["_embedded"][program]["showHref"] else None
            } for program in channel_schedule["programmes"]]

            schedule[channel.split("/")[7]] = programs
        logger.info(f"Schedule extracted for channel {channel_name} on date {date}")

        return schedule

    def get_video(self, video_id: str) -> dict:
        """
        Gets the metadata for a video with the given ID

        Parameters:
            video_id (str): The ID of the video to get the metadata for

        Returns:
            dict: The metadata for the video with the given ID
        """
        video_url = f"{self.BASE_URL}/api/v1/web/play/video/{video_id}"
        logger.info(f"Fetching video metadata for video {video_id}")
        video_metadata = utils.get_json(video_url)
        logger.info(f"Video metadata received for video {video_id}")

        logger.info(f"Extracting video info for video {video_id}")
        video_info = {
            "title": video_metadata["title"],
            "videoId": video_metadata["videoId"],
            "description": video_metadata["synopsis"],
            "url": video_metadata["page"]["url"],
            "duration": utils.convertDuration(video_metadata["duration"]),
            "rating": video_metadata["certification"],
            "coverImage": {
                "url": video_metadata["image"]["src"],
                "aspectRatio": video_metadata["image"]["aspectRatio"]
            },
            "videoType": video_metadata["videoType"],
            "onTime": video_metadata["onTime"],
            "offTime": video_metadata["offTime"],
            "showId": video_metadata["showHref"].split("/")[-1],
            "seasonNumber": video_metadata["seasonNumber"],
            "episodeNumber": video_metadata["episodeNumber"],
            "brightcove": {
                "videoId": video_metadata["publisherMetadata"]["brightcoveVideoId"],
                "accountId": video_metadata["publisherMetadata"]["brightcoveAccountId"],
                "playerId": video_metadata["publisherMetadata"]["brightcovePlayerId"]
            }
        }
        logger.info(f"Video info extracted for video {video_id}")

        return video_info

    def search(self, query: str) -> list:
        """
        Searches the TVNZ API for shows and movies matching the given query

        Parameters:
            query (str): The query to search for

        Returns:
            list: A list of shows and movies matching the given query
        """
        logger.info(f"Searching for query {query}")
        search_results = utils.get_json(f"{self.BASE_URL}/api/v1/web/play/search?q={query}&includeTypes=show")
        logger.info(f"Search results received for query {query}")
        results = []

        logger.info(f"Extracting search results for query {query}")
        for result in search_results["results"]:
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
        logger.info(f"Search results extracted for query {query}")

        return results

    def get_category(self, category_name: str) -> dict:
        """
        Gets the shows and movies in a category with the given name

        Parameters:
            category_name (str): The name of the category to get the shows and movies for

        Returns:
            dict: The shows and movies in the category with the given name
        """
        logger.info(f"Fetching category page for category {category_name}")
        category_page = utils.get_json(f"{self.BASE_URL}/api/v1/web/play/page/categories/{category_name}")
        category_info = {
            "title": category_page["title"],
            "description": category_page["metadata"]["description"],
            "url": category_page["url"],
            "shows": []
        }
        logger.info(f"Category page received for category {category_name}")

        logger.info(f"Extracting shows for category {category_name}")
        for show in category_page["layout"]["slots"]["main"]["modules"][0]["items"]:
            show_data = category_page["_embedded"][show["href"]]
            show_info = utils.process_show(show_data)
            category_info["shows"].append(show_info)
        logger.info(f"Shows extracted for category {category_name}")

        return category_info

    def get_all_show_ids(self) -> list:
        """
        Gets a list of all show and movie IDs

        Returns:
            list: A list of all show and movie IDs
        """
        logger.info("Fetching all show IDs")
        show_list = utils.get_json(f"{self.BASE_URL}/api/v1/web/play/shows")
        logger.info("Show IDs received")
        return [show.split("/")[-1] for show in show_list]

    def download_video(self, video_id: str, output: str) -> int:
        """
        Downloads a video with the given ID to the given output directory

        Parameters:
            video_id (str): The ID of the video to download
            output (str): The name and directory to save the video to (e.g. "D:/Downloads/video.mp4")

        Returns:
            int: 0 if the video was downloaded successfully, 1 if there was an error
        """

        # TODO: Implement a fully python-based solution for decrypting and combining the files

        # Get video info, specifically as the video's brightcove id and account id
        video_info = self.get_video(video_id)
        logger.info(f"Getting playback information for video {video_id}")
        playback_info_url = f"https://playback.brightcovecdn.com/playback/v1/accounts/{video_info['brightcove']['accountId']}/videos/{video_info['brightcove']['videoId']}"
        playback_info = utils.get_json(playback_info_url, headers={"Accept": f"application/json;pk={self.POLICY_KEY}"})
        logger.info(f"Playback information received for video {video_id}")

        # Get the decryption keys for the video
        license_url = playback_info["sources"][2]["key_systems"]["com.widevine.alpha"]["license_url"]
        mpd_url = playback_info["sources"][2]["src"].replace("http://", "https://")
        logger.info(f"Getting decryption keys for video {video_id}")
        decryption_keys = decrypter.getDecryptionKeys(mpd_url, license_url)
        logger.info(f"Decryption keys received for video {video_id}")

        # Download the video and audio files
        video_options = {
            'allow_unplayable_formats': True,
            'outtmpl': 'video/video.%(ext)s',
            'quiet': True,
            'no_warnings': True
        }
        video_downloader = yt_dlp.YoutubeDL(video_options)
        logger.info(f"Downloading video {video_id}")
        video_downloader.download([mpd_url])
        logger.info(f"Video {video_id} downloaded")

        # Rename the video files to remove the random text in the filename
        logger.info(f"Renaming video files")
        os.chdir("video")
        for file in os.listdir():
            os.rename(file, "video." + file.split(".")[-1])
        logger.info(f"Video files renamed")

        # Decrypt the video and audio files
        logger.info(f"Decrypting video and audio files")
        subprocess.run(['mp4decrypt', '--key', decryption_keys, 'video.m4a', 'audioDec.m4a'], check=True)
        subprocess.run(['mp4decrypt', '--key', decryption_keys, 'video.mp4', 'videoDec.mp4'], check=True)
        os.chdir("../")
        logger.info(f"Video and audio files decrypted")

        # Combine the video and audio files
        logger.info(f"Combining video and audio files")
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', 'video/videoDec.mp4', '-i',
                        'video/audioDec.m4a', '-c', 'copy', 'video/final.mp4'], check=True, shell=True)
        logger.info(f"Video and audio files combined")

        # Clean up the files
        logger.info(f"Cleaning up files")
        os.remove("video/video.m4a")
        os.remove("video/video.mp4")
        os.remove("video/videoDec.mp4")
        os.remove("video/audioDec.m4a")
        logger.info(f"Files cleaned up")

        # Move the final video to the output directory
        logger.info(f"Moving final video to output directory")
        shutil.move("video/final.mp4", output)
        logger.info(f"Final video moved to output directory")

        # Check if the file was downloaded successfully
        if os.path.exists(output):
            return 0
        else:
            return 1

    def get_subtitles(self, video_id: str) -> str:
        """
        Gets the subtitles for a video with the given ID

        Parameters:
            video_id (str): The ID of the video to get the subtitles for

        Returns:
            str: The subtitles for the video with the given ID
        """
        video_info = self.get_video(video_id)
        logger.info(f"Getting playback information for video {video_id}")
        playback_info_url = f"https://playback.brightcovecdn.com/playback/v1/accounts/{video_info['brightcove']['accountId']}/videos/{video_info['brightcove']['videoId']}"
        playback_info = utils.get_json(playback_info_url, headers={"Accept": f"application/json;pk={self.POLICY_KEY}"})
        logger.info(f"Playback information received for video {video_id}")

        # Get the subtitles url and download the subtitles
        logger.info(f"Downloading subtitles for video {video_id}")
        subtitles_url = playback_info["text_tracks"][0]["sources"][1]["src"]
        logger.info(f"Subtitles downloaded for video {video_id}")
        return self.session.get(subtitles_url).text

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
        logger.info("Attempting to get login ticket")
        auth = self.session.post("https://login.tvnz.co.nz/co/authenticate", headers={
            "Origin": "https://login.tech.tvnz.co.nz",
            "Referer": "https://login.tech.tvnz.co.nz"
        }, data={
            "client_id": "LnDAd4mARcCg8VnOhNmr22el46J91FmS",
            "credential_type": "password",
            "password": password,
            "username": email,
        })
        logger.info("Login ticket received")

        authentication = auth.json()

        # Access token request
        logger.info("Attempting to get access token")
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
        logger.info("Access token received")

        self.authorization = access_token.url.split("access_token=")[1].split("&")[0]

        return self.authorization

    @requires_login
    def get_user_info(self) -> list:
        """
        Gets the profile information for the logged-in user

        Returns:
            dict: The profile information for the logged-in user
        """
        logger.info("Fetching user info")
        profile_data = utils.get_json(f"{self.BASE_URL}/api/v1/web/consumer/account",
                                      headers={"Authorization": f"Bearer {self.authorization}"})
        logger.info("User info received")

        profiles = []

        logger.info("Extracting profiles")
        for profile in profile_data["profiles"]:
            profiles.append({
                "profile_id": profile["id"],
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
        logger.info("Profiles extracted")

        return profiles

    @requires_login
    def get_profile_icons(self) -> list:
        """
        Gets the profile icons available

        Returns:
            list: The profile icons available for use
        """
        logger.info("Fetching profile icons")
        profile_data = utils.get_json(f"{self.BASE_URL}/api/v1/web/consumer/profile-icons",
                                      headers={"Authorization": f"Bearer {self.authorization}"})
        logger.info("Profile icons received")

        icons = []

        logger.info("Extracting profile icons")
        for icon in profile_data["icons"]:
            icons.append({
                "url": icon["iconImage"]["src"],
                "aspectRatio": icon["iconImage"]["aspectRatio"]
            })
        logger.info("Profile icons extracted")

        return icons

    @requires_login
    def set_active_profile(self, profile_id: str) -> str:
        """
        Sets the active profile for the logged-in user

        Returns:
            str: The active profile ID
        """
        self.activeProfile = profile_id
        logger.info(f"Active profile set to {profile_id}")
        return self.activeProfile

    @requires_login
    def get_watched_videos(self) -> list:
        """
        Gets the videos the logged-in user has watched and the duration watched

        Returns:
            list: The videos the logged-in user has watched and the duration watched
        """

        logger.info("Fetching watched videos")
        watched_data = utils.get_json(f"https://apis-public-prod.tvnz.io/user/v1/play-state", headers={
            "Authorization": f"Bearer {self.authorization}",
            "x-tvnz-active-profile-id": self.activeProfile
        })
        logger.info("Watched videos received")

        watched_videos = []

        logger.info("Extracting watched videos")
        for video in watched_data["videos"]:
            watched_videos.append({
                "videoId": video["videoId"],
                "durationWatched": utils.convertDuration(video["duration"])
            })
        logger.info("Watched videos extracted")

        return watched_videos

    @requires_login
    def get_watchlist(self) -> list:
        """
        Gets the videos the logged-in user has added to their watchlist

        Returns:
            list: The videos the logged-in user has added to their watchlist
        """
        logger.info("Fetching watchlist")
        watch_list_data = utils.get_json(f"{self.BASE_URL}/api/v1/web/play/page/categories/my-list", headers={
            "Authorization": f"Bearer {self.authorization}",
            "x-tvnz-active-profile-id": self.activeProfile
        })
        logger.info("Watchlist received")

        watch_list_shows = []

        logger.info("Extracting watchlist shows")
        for show in watch_list_data["layout"]["slots"]["main"]["modules"][0]["items"]:
            show_data = watch_list_data["_embedded"][show["href"]]
            show_info = utils.process_show(show_data)
            watch_list_shows.append(show_info)
        logger.info("Watchlist shows extracted")

        return watch_list_shows

    @requires_login
    def add_to_watch_list(self, show_id: str) -> str:
        """
        Adds a show or movie to the logged-in user's watchlist

        Parameters:
            show_id (str): The ID of the show or movie to add to the watchlist

        Returns:
            str: The ID of the show or movie added to the watchlist
        """
        logger.info(f"Adding show {show_id} to watchlist")
        response = self.session.post(f"{self.BASE_URL}/api/v1/web/play/shows/{show_id}/preferences", headers={
            "Authorization": f"Bearer {self.authorization}",
            "x-tvnz-active-profile-id": self.activeProfile
        }, json={"isFavorite": True})

        if response.status_code == 200:
            logger.info(f"Show {show_id} added to watchlist")
            return show_id
        else:
            logger.error(f"Failed to add show {show_id} to watchlist")
            return ""

    @requires_login
    def remove_from_watch_list(self, show_id: str) -> str:
        """
        Removes a show or movie from the logged-in user's watchlist

        Parameters:
            show_id (str): The ID of the show or movie to remove from the watchlist

        Returns:
            str: The ID of the show or movie removed from the watchlist
        """
        logger.info(f"Removing show {show_id} from watchlist")
        response = self.session.post(f"{self.BASE_URL}/api/v1/web/play/shows/{show_id}/preferences", headers={
            "Authorization": f"Bearer {self.authorization}",
            "x-tvnz-active-profile-id": self.activeProfile
        }, json={"isFavorite": False})

        if response.status_code == 200:
            logger.info(f"Show {show_id} removed from watchlist")
            return show_id
        else:
            logger.error(f"Failed to remove show {show_id} from watchlist")
            return ""