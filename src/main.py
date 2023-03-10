import time
import winsound

from src.download import Downloader
from src.edit import Editor
from src.instagram_scraper import InstagramScraper
from src.upload import Uploader
from src.youtube_scraper import YoutubeScraper


def main():
    # Keep track of how much time it takes
    start = time.time()

    # Select what to do
    youtube_scraping = False
    instagram_scraping = False
    download = False
    edit = False
    upload = True

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
        Downloader.download_youtube()
        # Downloader.download_instagram()

    # Get the needed frames in the videos with OpenCV
    if edit:
        Editor.get_images()
        # Editor.compare_videos()

    # Upload videos using Google Drive API
    if upload:
        Uploader.upload()

    # Notify with a sound that the program has finished
    print(time.time() - start)
    duration = 1000
    freq = 400
    winsound.Beep(freq, duration)


if __name__ == '__main__':
    main()
