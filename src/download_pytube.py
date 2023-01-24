from pytube import YouTube


class Downloader:
    def __init__(self, df):
        self.df = df
        self.download()

    def download(self) -> None:
        """
        Using Pytube downloads the URLs in the given csv file
        """
        for link in self.df.loc[:, "URL"]:
            yt = YouTube(link)
            yt = yt.streams.get_highest_resolution()
            yt.download("./videos")
