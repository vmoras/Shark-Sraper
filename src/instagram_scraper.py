from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement

import pandas as pd
import time
from random import randint


class InstagramScraper:
    def __init__(self):
        self.driver = self._set_driver()
        self.wait = self._set_wait()
        self.SCROLL_PAUSE_TIME = 2
        self.URLs = set()

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

    def get_info(self) -> None:
        """
        Creates a csv file with the link of each video from Instagram
        that will be used for downloading. Those videos had the word shark
        in their description and are from The Malibu Artists
        """
        self._get_URLs()
        self._get_link_videos()
        self.driver.quit()

    def _get_URLs(self) -> None:
        """
        Updates the URLs set with the URL of the posts with videos from all the
        profile of The Malibu Artists.

        Instagram loads its posts in a weird way. The HTML has around 20
        rows, each one with 3 videos. When the user scrolls down, that list of
        20 rows gets updated, so in one point the last post will be the first
        post in the HTML. This will be used to get all the videos. The url of the third
        post from last to first is saved. Then, scrolls down until that post is the
        first one in the HTML, it means the rest of the rows in the HTML has new posts,
        so the third is saved and the loop repeats. This is done until it gets to the last
        post (which was selected by me) where there are no other shark videos from that one
        to the first ever post.
        """
        # To prevent banning from YouTube some random sleeps are used,
        # from i to j seconds
        i, j = 2, 4

        # Open instagram and wait until it loads
        self.driver.get("https://www.instagram.com")
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "button")))

        # Log in
        self._login(i, j)

        # Search for The Malibu Artist
        time.sleep(randint(i, j))
        self.driver.get("https://www.instagram.com/themalibuartist/?hl=en")
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "article")))

        # Get the first videos and the last one (third from last to first) in that section
        box_videos = self.driver.find_element(By.TAG_NAME, "article")
        videos = box_videos.find_elements(By.TAG_NAME, "a")
        last_video = videos[-3].get_attribute("href")

        # Save all the urls of each post
        info_videos = []
        last_videos, stop = self._get_video_info(videos)
        info_videos.extend(last_videos)

        # The scroll height from a mouse is around 100
        scroll_height = 100
        move = self.driver.execute_script("return document.documentElement.scrollHeight")
        while True:
            # Scrolls down
            move += scroll_height
            self.driver.execute_script(f"window.scrollTo(0, {move});")
            time.sleep(0.5)

            # Get the first post in the HTML
            first_video = box_videos.find_element(By.TAG_NAME, "a").get_attribute("href")

            # It means there are new posts in the HTML
            if first_video == last_video:
                move += scroll_height
                self.driver.execute_script(f"window.scrollTo(0, {move});")
                time.sleep(0.5)

                # Get those new posts and update the last video
                videos = box_videos.find_elements(By.TAG_NAME, "a")
                last_videos, stop = InstagramScraper._get_video_info(videos)
                self.URLs.update(last_videos)
                last_video = videos[-3].get_attribute("href")

            # From this post there are no more useful videos
            if stop:
                print("No more videos")
                break

    @staticmethod
    def _get_video_info(videos: list[WebElement]) -> tuple[list[str], bool]:
        """
        Returns a tuple: a list with the link for each video (which will be used
        later to download the video) and a boolean indicating if the search should
        continue or stop (in other words, if the last post is in this search or not).
        """
        # The last video is not the last post but, from this video there are no
        # more shark videos, so, the other posts are not useful
        last_video = "https://www.instagram.com/p/B89veJsgwSt/?hl=en"

        info = []
        stop = False
        for video in videos:
            link = video.get_attribute("href")
            try:
                # Check if the post is a video using the tag svg (which is an icon on the
                # top left side) and the attribute Clip. Other posts with multiple images
                # have the tag svg but their attribute has other value.
                icon = video.find_element(By.TAG_NAME, "svg")
                if icon.get_attribute("aria-label") == "Clip":
                    info.append(link)

            # The post was an image
            except NoSuchElementException:
                pass

            # We are in the last video, the search must stop
            if link == last_video:
                stop = True

        return info, stop

    def _get_link_videos(self) -> None:
        """
        Saves a csv with the links of the videos which will be used for downloading.
        To do this, each post is open, then if the word shark is in the description the
        link for the video is saved
        """
        search_words = ["shark", "sharks", "great white", "Shark", "Sharks", "Great White"]
        updated_info = []

        num = 1
        total = len(self.URLs)

        for URL in self.URLs:
            # Get each post, and wait a random time to prevent banning
            self.driver.get(URL)
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "video")))
            time.sleep(randint(2, 4))

            # The post has no description, no way to know if there is a shark or not
            try:
                description = self.driver.find_element(By.TAG_NAME, "h1").text
            except NoSuchElementException:
                continue

            # The word shark was on the description, then the link must be saved
            if any(word in description for word in search_words):
                video = self.driver.find_element(By.TAG_NAME, "video")
                link = video.get_attribute("src")

                video_info = {
                    "Channel Name": "TheMalibuArtist",
                    "Video Name": "NN",
                    "URL": link,
                    "Description": description
                }

                updated_info.append(video_info)

            print(f"Done {num}/{total}")
            num += 1

        df = pd.DataFrame(updated_info)
        df.to_csv("InstagramVideos.csv")

    def _login(self, i: int, j: int) -> None:
        """
        Logs into Instagram. There are multiple sleeps, this is to prevent
        a ban from Instagram, it allows the program to act more like a human.

        The sleep will be a random number from i to j (inclusive)
        """
        # Get user and password
        username = self.driver.find_element(By.CSS_SELECTOR,
                                            "input[name='username']")
        password = self.driver.find_element(By.CSS_SELECTOR,
                                            "input[name='password']")

        # Clear those cells and put the info
        username.clear()
        time.sleep(randint(i, j))
        username.send_keys("vmoraserrano@gmail.com")

        password.clear()
        time.sleep(randint(i, j))
        password.send_keys("Mserrano2019")

        # Click on submit
        time.sleep(randint(i, j))
        self.driver.find_element(By.CSS_SELECTOR,
                                 "button[type='submit']").click()

        # Wait until the Main page is loaded. It always asks
        # if we want to save the login, or activate notification
        self.wait.until(EC.presence_of_element_located((By.XPATH,
                                                        "//button[contains(text(), 'Not Now')]")))
