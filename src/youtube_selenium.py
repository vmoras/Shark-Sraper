import time
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class YoutubeScraper:
    def __init__(self):
        self.approved_channels = self.set_approved_channels()
        self.disapproved_titles = self.set_disapproved_titles()
        self.search_words = self.set_search_words()
        self.driver = self.set_driver()
        self.wait = self.set_wait()
        self.SCROLL_PAUSE_TIME = 1.5
        self.df = None

    @staticmethod
    def set_approved_channels() -> set:
        """
        Returns the name of the approved channels from the txt file
        """
        with open("lib/ApprovedChannels.txt") as file:
            approved_channels = {line.rstrip() for line in file}

        return approved_channels

    @staticmethod
    def set_disapproved_titles() -> set:
        """
        Returns the name of the disapproved titles inside the
        approved channels
        """
        with open("lib/DisapprovedTitles.txt") as file:
            disapproved_titles = {line.rstrip() for line in file}
            return disapproved_titles

    @staticmethod
    def set_search_words() -> set:
        """
        Returns the main words used to make the search
        """
        words = {"shark", "great white", "sharks", "great whites"}
        return words

    @staticmethod
    def set_driver() -> webdriver:
        """
        Initializes and returns the Firefox driver
        """
        path = "lib/geckodriver.exe"
        return webdriver.Firefox(service=Service(executable_path=path))

    def set_wait(self) -> WebDriverWait:
        """
        Initializes and returns the web driver used for explicit waits
        """
        seconds = 5
        return WebDriverWait(self.driver, seconds)

    def get_info(self) -> None:
        """
        Recollect and save the web pages info, such as Channel, title and url

        1) Get videos from the approved channels
        2) Get videos from the rest of YouTube
        3) Save all the info into a csv file
        """
        self.get_approved_channels()
        self.driver.quit()
        self.save_df()

    def get_approved_channels(self) -> None:
        """
        Updates the data frame with the channel name, video title and url for
        each video in the approved channels. Here the only words to find are shark or
        great white. There is no need to check if the video or its description has the
        word drone, since they are already approved channels
        """
        videos_list = []
        for channel in self.approved_channels:
            self.driver.get(f"https://www.youtube.com/@{channel}/videos")
            self.wait.until(EC.presence_of_all_elements_located((By.ID, "video-title")))
            channel_title = self.driver.find_element(By.ID, "channel-name").text

            # Scroll down all the web page to the bottom
            while True:
                scroll_height = 1500
                height_before = self.driver.execute_script("return document.documentElement.scrollHeight")
                self.driver.execute_script(f"window.scrollTo(0, {height_before} + {scroll_height});")
                time.sleep(self.SCROLL_PAUSE_TIME)
                height_after = self.driver.execute_script("return document.documentElement.scrollHeight")

                if height_before == height_after:
                    break

            # Gets each video in the chanel
            videos = self.driver.find_elements(By.ID, "video-title-link")
            for video in videos:
                video_title = video.text + " "

                # If the video has the words shark or great white, and it is not in the disapproved titles, save it
                if any(word in video_title.lower() for word in self.search_words):
                    if not any(title.lower() + " " == video_title.lower() for title in self.disapproved_titles):
                        video_item = {
                            "Channel Name": channel_title,
                            "Video Name": video.text,
                            "URL": video.get_attribute("href")
                        }
                        videos_list.append(video_item)

        # Save the results
        self.df = pd.DataFrame(videos_list)

    def get_other_channels(self) -> None:
        """
        TODO: get the other channels with Pytube
        updates the data frame with videos from channels different of the approved ones or the
        disapproved ones
        """

    def save_df(self) -> None:
        """
        Save the data frame into a csv file
        """
        self.df.to_csv("lib/safeVideos.csv")
