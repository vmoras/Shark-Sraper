import os

from src.youtube_scraper import YoutubeScraper
from src.instagram_scraper import InstagramScraper
from src.download import Downloader
from src.edit import Editor
from src.upload import Uploader


def main():
    # Select what to do
    youtube_scraping = False
    instagram_scraping = False
    download = True
    edit = False
    upload = False

    # Get videos info from YouTube using selenium and Pytube
    if youtube_scraping:
        YTScraper = YoutubeScraper()
        YTScraper.get_info()

    # Get videos info from Instagram using
    if instagram_scraping:
        InstScraper = InstagramScraper()
        InstScraper.get_info()

    # Download raw_videos using Pytube
    if download:
        # Downloader.download_youtube()
        Downloader.download_instagram()

    # Get the needed frames in the videos with OpenCV
    if edit:
        Editor.get_images()

    # Upload videos using Google Drive API
    if upload:
        Uploader.upload()

    print("WE ARE DONE!")


if __name__ == '__main__':
    main()
