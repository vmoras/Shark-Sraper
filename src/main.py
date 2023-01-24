from src.youtube_selenium import YoutubeScraper
from src.youtube_pytube import YoutubePytube
from src.youtube_api import YoutubeAPI
from src.download_pytube import Downloader

import pandas as pd


def main():
    # For debugging
    selenium = False
    API = False
    pytube = False
    download = True

    # Get videos info using selenium
    if selenium:
        info_scraper = YoutubeScraper()
        info_scraper.get_info()

    # Get videos info using YouTube API: Won't work since you need your own API_KEY
    if API:
        info_api = YoutubeAPI()
        info_api.get_info()

    # Get videos info using Pytube
    if pytube:
        info_pytube = YoutubePytube()
        info_pytube.get_info()

    # Download videos using Pytube
    if download:
        df = pd.read_csv('tests/testVideos.csv')
        Downloader(df)

    print("Done")


if __name__ == '__main__':
    main()


"""
TODO 
    - Pytube has a weird bug where it repeats the same videos more than once
    - Use ThreadPool to optimize the downloads
    - Use category id to avoid videos such as Shark Tank
    - From non-approved videos check if some of them could be approved
    - Find a way to avoid repeated videos: you could use the upload day and length -> specially for news
    - Fix Unexpected render encountered while using pytube
    
    - How much data do we need? Search until there are no available videos in the gotten page? 
    - Does the videos need sound? You could make them lighter
    - Is there a problem if there is people on the video? NO idea how to avoid it 
    - The description has the word drone but no drone was used: like in the White Shark Video channel
    - Is it useful to have the location of the video?
"""