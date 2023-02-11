import requests
from pytube import YouTube
import pandas as pd
import numpy as np
import concurrent.futures


class Downloader:
    @staticmethod
    def download_youtube() -> None:
        """
        Creates threads where each one will download a chunk of videos
        from the CSV file
        """
        # Get file name and its length
        df = pd.read_csv('YouTubeVideos.csv', index_col=0)

        # First and last index of the videos to be downloaded and the number of
        # Threads
        first = 0
        last = len(df.index)
        threads = 1

        # Split the videos for each thread
        array = np.array_split(range(first, last + 1), threads)
        groups = [(chunk[0], chunk[-1]) for chunk in array]

        # Start the threads
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(Downloader._get_videos_youtube, groups)

    @staticmethod
    def _get_videos_youtube(slicing: tuple) -> None:
        """
        Using Pytube downloads the URLs in the given csv file
        """
        df = pd.read_csv("YouTubeVideos.csv", index_col=0)

        # Index of the first and last video to be downloaded
        begin = slicing[0]
        end = slicing[1]
        row = begin

        # Get each video and download it
        for link in df.loc[begin: end, "URL"]:
            youtube = YouTube(link)

            # The videos with high resolution (such as 1440p or 2160p) have the
            # video and audio separated (adaptive streams), those with the audio
            # and video together have a lower resolution.So in order to get the
            # best resolutions filter only the streams with video.
            streams = youtube.streams.filter(only_video=True)
            max_resolution = 0
            yt = None

            for stream in streams:

                # Get the video with the highest resolution
                # Pytube has this method, but sometimes it does not work
                try:
                    resolution = int(stream.resolution[:-1])
                    if resolution > max_resolution:
                        max_resolution = resolution
                        yt = stream

                # The streams object from Pytube has a bug, and sometimes stream is None
                # or does not have a resolution, etc
                except:
                    pass

            # Depending on the extension save the file in a convert_videos folder (which later
            # will be converted to mp4) or in the raw_videos folder (which is the final video)
            output_folder = "./videos"

            # Download the video in the given folder with its name being its
            # row in the csv file
            print(f"Downloading video number: {row}")
            yt.download(
                output_path=output_folder,
                filename=f"{row}.{yt.subtype}"
            )
            print(f"       Done video number: {row}")

            row += 1

    @staticmethod
    def download_instagram() -> None:
        """
        Downloads the videos from Instagram using requests. Those
        videos have sound and are not 4K since Instagram does not support
        them. Instead, they are max 1080p
        """
        # Get info from file
        df = pd.read_csv("InstagramVideos.csv", index_col=0)

        # The file will be downloaded in chunks of 1024, since it would be
        # too heavy for python to get big files all in once
        chunk_size = 1024

        links = [link for link in df["URL"]]
        row = 0

        for link in links:
            # Get the video
            r = requests.get(link, stream=True)

            # Save the video
            with open(f"./IVideos/{row}.mp4", "wb") as f:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    f.write(chunk)

            print(f"Done video {row}")

            row += 1
