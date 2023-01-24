from pytube import Search
import pandas as pd


class YoutubePytube:
    def __init__(self):
        self.omitted_channels = self.get_omitted_channels()
        self.df = None

    @staticmethod
    def get_omitted_channels() -> str:
        """
        Returns a string with the name of the channels that won't be search since they are already part of
        the approved channels or disapproved channels. It has a '-' at the beginning of each name so the YouTube
        search engine will avoid getting those words.
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

    def get_info(self) -> None:
        """
        Gathers the main info (title name, channel name and url) for all the videos
        and saves it in a csv file
        """
        self.get_approved_channels()
        self.get_other_channels()
        self.save_df()

    def get_approved_channels(self) -> None:
        """
        TODO: get the approved channels with Pytube
        Updates the main data frame with videos from the approved channels
        """
        pass

    def get_other_channels(self) -> None:
        """
        Updates the main data frame with videos from channels different of the approved ones or the
        disapproved ones
        """
        # What will be searched in the YouTube search engine
        q = f'shark footage drone {self.omitted_channels}'

        videos_list = []
        num_searches = 2
        for _ in range(num_searches):
            search = Search(q)
            for video in search.results:

                # If the video is a short, omit it
                if video.description is None:
                    continue
                description = video.description.lower()

                # Make sure the word shark is in the title and drone in the title or description
                title = video.title.lower()
                if "shark" in title and ("drone" in title or "drone" in description):

                    # FIXME Weird bug: The Rogue Droner is still appearing despite being on the omit_channels
                    if video.author != "The Rogue Droner":
                        video_item = {
                            "Channel Name": video.author,
                            "Video Name": video.title,
                            "URL": f"https://www.youtube.com/watch?v={video.video_id}",
                        }
                        videos_list.append(video_item)

            # Get the next page of results
            search.get_next_results()

        # Save the results in the main data frame
        self.df = pd.DataFrame(videos_list)

    def save_df(self) -> None:
        """
        Save the main data frame into a csv file
        """
        self.df.to_csv("lib/notSafeVideos.csv")
