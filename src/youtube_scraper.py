import pandas as pd
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pytube import YouTube, Channel, Search

from googleapiclient.discovery import build


class YoutubeScraper:
    def __init__(self):
        self.approved_channels = self._set_approved_channels()
        self.omitted_channels = self._set_omitted_channels()
        self.disapproved_titles = self._set_disapproved_titles()
        self.search_words = self._set_search_words()
        self.driver = self._set_driver()
        self.wait = self._set_wait()
        self.SCROLL_PAUSE_TIME = 2
        self.df_approved = None
        self.df_pytube = None
        self.df_selenium = None

    @staticmethod
    def _set_approved_channels() -> set:
        """
        Returns the name of the approved channels from the txt file
        """
        with open("lib/ApprovedChannels.txt") as file:
            approved_channels = {line.rstrip() for line in file}

        return approved_channels

    @staticmethod
    def _set_disapproved_titles() -> set:
        """
        Returns the name of the disapproved titles inside the
        approved channels
        """
        with open("lib/DisapprovedTitles.txt") as file:
            disapproved_titles = {line.rstrip() for line in file}
            return disapproved_titles

    @staticmethod
    def _set_search_words() -> set:
        """
        Returns the main words used to make the search
        """
        words = {"shark", "great white", "sharks", "great whites"}
        return words

    @staticmethod
    def _set_omitted_channels() -> str:
        """
        Returns a string with the name of the channels that won't be search since they are already part
        of the approved channels or disapproved channels. It has a '-' at the beginning of each name so
        the YouTube search engine will avoid getting those words.
        """
        # Extract names for the approved and disapproved channels in txt files
        with open("lib/ApprovedChannels.txt") as file:
            approved_channels = [line.rstrip() for line in file]

        with open("lib/DisapprovedChannels.txt") as file:
            disapproved_channels = [line.rstrip() for line in file]

        # Change hydrophilik name: remove the 6s at the end
        approved_channels = [channel.replace("6666", "") for channel in approved_channels]

        # Add '-' at the beginning of each channel name
        omitted_channels = []
        for channel in approved_channels:
            omitted_channels.append(f"-{channel} ")
        for channel in disapproved_channels:
            omitted_channels.append(f"-{channel} ")

        # Get them together in a string
        phrase = "".join(omitted_channels)
        return phrase

    @staticmethod
    def _set_driver() -> webdriver:
        """
        Initializes and returns the Firefox driver
        """
        path = "lib/geckodriver.exe"
        return webdriver.Firefox(service=Service(executable_path=path))

    def _set_wait(self) -> WebDriverWait:
        """
        Initializes and returns the web driver used for explicit waits
        """
        seconds = 5
        return WebDriverWait(self.driver, seconds)

    def _scroll_down(self) -> None:
        """
        Moves down the window and waits until YouTube provides more videos. Keeps scrolling
        until reaches the end of the webpage
        """
        while True:
            scroll_height = 1500
            height_before = self.driver.execute_script("return document.documentElement.scrollHeight")
            self.driver.execute_script(f"window.scrollTo(0, {height_before} + {scroll_height});")
            time.sleep(self.SCROLL_PAUSE_TIME)
            height_after = self.driver.execute_script("return document.documentElement.scrollHeight")

            if height_before == height_after:
                break

    def get_info(self) -> None:
        """
        Recollect and save the web pages info, such as Channel, title and url

        1) Get videos from the approved channels
        2) Get videos from the rest of YouTube with Selenium
        3) Get videos from the rest of YouTube with Pytube
        4) Get videos in spanish and portuguese
        5) Merge all the info into a csv file
        """
        self._get_approved_channels()
        self._get_other_channels_selenium()
        self.driver.quit()
        self._get_other_channels_pytube()
        self._merge_save_csv()

    def _get_approved_channels(self) -> None:
        """
        Updates a data frame with the channel name, video title and url for
        each video in the approved channels. Here the only words to find are shark or
        great white. There is no need to check if the video or its description has the
        word drone, since they are already approved channels. It uses Selenium
        """
        print("Approved Channels:")
        videos_list = []
        for channel in self.approved_channels:
            self.driver.get(f"https://www.youtube.com/@{channel}/videos")
            self.wait.until(EC.presence_of_all_elements_located((By.ID, "video-title")))
            channel_title = self.driver.find_element(By.ID, "channel-name").text

            # Scroll down all the web page to the bottom
            self._scroll_down()

            # Gets each video in the chanel
            videos = self.driver.find_elements(By.ID, "video-title-link")
            for video in videos:
                # Add a space at the end and change the title to lowercase, so it can be compared with
                # the search_words (in other words, to be case-insensitive)
                video_title = video.text + " "
                video_title = video_title.lower()

                # If the video has the words shark or great white, and it is not
                # in the disapproved titles, save it
                if any(word in video_title for word in self.search_words):
                    if not any(title.lower() + " " == video_title for title in self.disapproved_titles):
                        video_item = {
                            "Channel Name": channel_title,
                            "Video Name": video.text,
                            "URL": video.get_attribute("href")
                        }
                        videos_list.append(video_item)

            print(f"    Done channel {channel_title}")

        # Save the results
        self.df_approved = pd.DataFrame(videos_list)

    def _get_other_channels_selenium(self) -> None:
        """
        updates a data frame with videos from channels different of the approved ones or the
        disapproved ones. Uses Selenium
        """
        print("Other Channels Selenium:")
        videos_list = []

        q = f'shark+footage+drone+{self.omitted_channels}'

        self.driver.get(f"https://www.youtube.com/results?search_query={q}")
        self.wait.until(EC.presence_of_all_elements_located((By.ID, "video-title")))

        # Scroll down all the web page to the bottom
        self._scroll_down()

        # Gets each video in the page
        videos = self.driver.find_elements(By.ID, "video-title")
        current_video = 0
        for video in videos:
            link = video.get_attribute("href")
            if link is None:
                continue

            # Add a space at the end and change the title to lowercase, so it can be compared with
            # the search_words (in other words, to be case-insensitive)
            video_title = video.text + " "
            video_title = video_title.lower()

            if any(word in video_title for word in self.search_words):
                yt = YouTube(link)
                description = yt.description

                # If the video is a short, omit it
                if yt.description is None:
                    continue

                if any(word in video_title for word in ["drone", "Drone"]
                       ) or any(word in description for word in ["drone", "Drone"]):
                    if yt.channel_id is None:
                        channel_name = "None"
                    else:
                        channel = Channel(yt.channel_url)
                        channel_name = channel.channel_name

                    video_item = {
                        "Channel Name": channel_name,
                        "Video Name": video.text,
                        "URL": video.get_attribute("href")
                    }
                    videos_list.append(video_item)

            print(f"    Done video {current_video} / {len(videos)}")
            current_video += 1

        self.df_selenium = pd.DataFrame(videos_list)

    def _get_other_channels_pytube(self) -> None:
        """
        Updates a data frame with videos from channels different of the approved ones or the
        disapproved ones. Uses Pytube
        """
        print("Other Channels Pytube:")
        # What will be searched in the YouTube search engine
        q = f'shark footage drone {self.omitted_channels}'

        # Main list used later to create the data frame
        videos_list = []

        # There will be videos which are no useful, this will be used to determinate
        # when the search is over. If there are n searches without a useful video, stop
        stop = 2
        no_videos = 0

        # Create the search object and range of the result list
        search = Search(q)
        first_video = 0
        last_video = len(search.results)

        # Iterate until there are n search without a useful video
        while no_videos < stop:
            useful_video = False
            for i in range(first_video, last_video):
                video = search.results[i]

                # If the video is a short, omit it
                if video.description is None:
                    continue
                description = video.description.lower()

                # Make sure the word "shark" is in the title and "drone" is in the title or description
                title = video.title.lower()
                if "shark" in title and ("drone" in title or "drone" in description):
                    video_item = {
                        "Channel Name": video.author,
                        "Video Name": video.title,
                        "URL": f"https://www.youtube.com/watch?v={video.video_id}",
                    }
                    videos_list.append(video_item)

                    # There is at least one useful video in this search
                    useful_video = True

            # Not a single useful video in this search, so add the count
            if not useful_video:
                no_videos += 1

            # Get the next page of results
            try:
                search.get_next_results()
            except IndexError:
                print("There are no more videos")
                break

            # Update range
            first_video, last_video = last_video, len(search.results)

            print(f"    Done {last_video} videos")

        # Save the results in the main data frame
        self.df_pytube = pd.DataFrame(videos_list)

    def _merge_save_csv(self) -> None:
        """
        Merge the 3 different data frames, remove duplicates using the
        URL, convert it to csv and save it.
        """
        df_final = pd.concat([self.df_selenium, self.df_pytube, self.df_approved], ignore_index=True)
        df_final.drop_duplicates(subset=["URL"], ignore_index=True, inplace=True)

        df_final.to_csv("YouTubeVideos.csv")
