from googleapiclient.discovery import build
import pandas as pd


class YoutubeAPI:
    """
    WON'T BE USED SINCE IT HAS A LIMIT
    """

    def __init__(self):
        self.API_key = "GET_YOUR_OWN_API_KEY"
        self.youtube = build("youtube", "v3", developerKey=self.API_key)

    @staticmethod
    def get_omitted_channels() -> str:
        omitted_channels = ["-DroneSharkApp ", "-SouthForkSalt ", "-GreatWhiteDronE ",
                            "-Theroguedroner ", "-hydrophilik ", "-TheMalibuArtist ",
                            "-UltimateDroneFishing "]

        phrase = "".join(omitted_channels)
        return phrase

    def get_info(self) -> None:
        omitted_channels = self.get_omitted_channels()
        token = "CAEQAA"
        videos_list = []

        for _ in range(20):
            request = self.youtube.search().list(
                part="id, snippet",
                maxResults=50,
                pageToken=token,
                q=f'"shark" footage "drone" {omitted_channels}',
            )
            response = request.execute()
            for item in response["items"]:
                if item["id"]["kind"] == "youtube#video":
                    video_item = {
                        "Channel Name": item["snippet"]["channelTitle"],
                        "Video Name": item["snippet"]["title"],
                        "URL": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    }
                    videos_list.append(video_item)
            token = response["nextPageToken"]

        # Save the results
        df = pd.DataFrame(videos_list)
        df.to_csv("lib/otherVideos.csv")
