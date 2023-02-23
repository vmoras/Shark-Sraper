from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement

import pandas as pd
import time
from random import randint


class InstagramScraper:
    def __init__(self):
        self.driver = self._set_driver()
        self.wait = self._set_wait()
        self.SCROLL_PAUSE_TIME = 2
        self.URLs = list()

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
        seconds = 30
        return WebDriverWait(self.driver, seconds)

    def get_info(self) -> None:
        """
        Creates a csv file with the link of each video from Instagram
        that will be used for downloading. Those videos will be presented
        to the programmer, so they decided whether it used a drone or not,
        so it can be saved.

        The best is to do the process in two steps. In the first one, you get
        all the URLs, and in the second one, each URL is open.
        """
        profiles_info = [
            "themalibuartist", "scott_fairchild", "nat_davies_",
            "wanderlust_flyer", "sharkyaerials"
        ]

        # Open instagram and wait until it loads
        self.driver.get("https://www.instagram.com/")
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "button")))

        # Log in
        self._login(2, 4)

        # FIRST STEP
        # for profile in profiles_info:
            # self._get_URLs(profile)

        # Save the current URLs in case Instagram decides to die
        # with open("urls.txt", "w") as f:
            # for url in self.URLs:
                # f.write(f"{url}\n")

        # SECOND STEP
        # Open the saved URLs
        # self.URLs = list(line.strip() for line in open("urls.txt"))
        # self.URLs = self.URLs[:]
        # self._get_link_videos()

        self.driver.quit()

    def _get_URLs(self, profile: str) -> None:
        """
        Updates the URLs list with the URLs of the posts with all the videos
        of the given profile

        Instagram loads its posts in a weird way. The DOM has around 20
        rows, each one with 4 videos. When the user scrolls down, that list of
        20 rows gets updated, so in one point the last post will be the first
        post in the DOM. This will be used to get all the videos. The url of the fourth
        post from last to first is saved. Then, scrolls down until that post is the
        first one in the DOM, it means the rest of the rows in the DOM has new posts,
        so the fourth is saved and the loop repeats. This is done until it gets to the last
        post (which was selected by me) where there are no other shark videos from that one
        to the first ever post.
        """
        # To prevent banning from Instagram some random sleeps are used,
        # from i to j seconds
        i, j = 2, 4

        # Search for a profile
        time.sleep(randint(i, j))
        self.driver.get(f"https://www.instagram.com/{profile}/reels/")
        time.sleep(3)

        # Get the first videos and the last one (third from last to first) in that section
        box_videos = self.driver.find_elements(By.XPATH, "//main/div/div")[2]
        videos = box_videos.find_elements(By.TAG_NAME, "a")
        last_video = videos[-4].get_attribute("href")

        # Save all the urls of each post
        info_videos = []
        last_videos = self._get_video_info(videos)
        info_videos.extend(last_videos)

        # The scroll height from a mouse is around 100. To know we are in the bottom of the
        # page, if we scroll 40 times and there are no new posts (line 122) then it is over.
        move = 100
        scrolls = 0
        while True:
            # Scrolls down
            scrolls += 1
            self.driver.execute_script(f"window.scrollBy(0, {move});")
            time.sleep(0.3)

            # Get the first post in the HTML
            first_video = box_videos.find_element(By.TAG_NAME, "a").get_attribute("href")

            # It means there are new posts in the HTML
            if first_video == last_video:
                self.driver.execute_script(f"window.scrollBy(0, {move});")
                time.sleep(0.3)

                # Get those new posts and update the last video
                videos = box_videos.find_elements(By.TAG_NAME, "a")
                last_videos = InstagramScraper._get_video_info(videos)
                self.URLs.extend(last_videos)
                last_video = videos[-4].get_attribute("href")

                scrolls = 0

            # It is the end of the webpage
            if scrolls == 40:
                videos = box_videos.find_elements(By.TAG_NAME, "a")
                last_videos = InstagramScraper._get_video_info(videos)
                self.URLs.extend(last_videos)
                print(f"No more videos. Done {profile}. Total videos {len(self.URLs)}")
                break

    @staticmethod
    def _get_video_info(videos: list[WebElement]) -> list[str]:
        """
        Returns the href (link later used to get the post and the video) for each
        video in the videos list.
        """
        info = []
        for video in videos:
            link = video.get_attribute("href")
            info.append(link)
        return info

    def _get_link_videos(self) -> None:
        """
        Saves a csv with the links of the videos which will be used for downloading.
        To do this, each post is open, then if the programmer decides to save the video
        they input "T", which means that video will be saved, otherwise it will not.

        Sometimes Instagram crashes, so to avoid losing all the info, once an exception
        happens, the links of the viewed posts are saved.
        """
        updated_info = []
        num = 0
        for URL in self.URLs:
            # Get each post, and wait a random time to prevent banning
            try:
                # Wait until de descriptions loads
                self.driver.get(URL)
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "article")))

                # Get the name of the profile from the article tag
                profile_long = self.driver.find_element(By.TAG_NAME, "article").text
                profile = profile_long.split("\n")[0]

                # Sometimes the info is different, so the name of the profile is the second
                # value in the list
                if profile == "0:00":
                    profile = profile_long.split("\n")[1]

                # Saved the video if there are any sharks, and they used a drone
                s = input("Save video? ")

                # The programmer decided to save the video
                if s == "T":
                    video = self.driver.find_element(By.TAG_NAME, "video")
                    link = video.get_attribute("src")

                    video_info = {
                        "Channel Name": profile,
                        "Video Name": "NN",
                        "URL": URL,
                        "Download": link,
                    }
                    updated_info.append(video_info)

                num += 1

                time.sleep(randint(1, 3))

            # Some problem happened, save the info
            except:
                df = pd.DataFrame(updated_info)
                df.to_csv("backup.csv")
                print(f"Watched videos: {num}")

        # There was no problem or exception, save the info
        df = pd.DataFrame(updated_info)
        df.to_csv("backup2.csv")

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
