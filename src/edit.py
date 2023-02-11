import cv2
import ffmpeg
import os
import concurrent.futures
import numpy as np
import pandas as pd


class Editor:
    @staticmethod
    def get_images() -> None:
        """
        Creates threads where each one will download an interval of frames
        from a video
        """
        # Get the number of videos in the folder
        num_videos = len(os.listdir("./videos"))
        first = 2
        last = 5
        threads = 1

        # Split the videos for each thread
        array = np.array_split(range(first, last + 1), threads)
        groups = []
        for chunk in array:
            groups.append((chunk[0], chunk[-1]))

        # Start the threads
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(Editor._extract_frames_range, groups)

    @staticmethod
    def _extract_frames_range(slicing: tuple) -> None:
        """
        Saves the frames from a given range of seconds. The input are the seconds to remove,
        in other words, the intervals between each range are the frames to obtain.
        """
        # Set directory and Data Frame with the info
        directory = "./videos"
        df = pd.read_csv("Videos.csv", index_col=0)

        # Range of videos to be open
        begin = slicing[0]
        end = slicing[1]

        # Get the intervals for each video, each video will have a list of tuples with the
        # beginning and ending seconds of the interval
        seconds_videos = df.loc[begin:end, "Seconds"].tolist()
        seconds_list = [list(seconds.split(",")) for seconds in seconds_videos]
        seconds = []
        for seconds_video in seconds_list:
            ranges_video = [tuple(map(int, interval.split("-"))) for interval in seconds_video]
            seconds.append(ranges_video)

        # For each video in the given range (depends on each thread) find it and get its frames
        for row in range(begin, end + 1):
            video_id = df.loc[row, "URL"]
            video_id = video_id[32:]

            # Check whether the file has an extension mp4 or webm
            if os.path.exists(f"{directory}/{row}.mp4"):
                filename = f"{row}.mp4"
            else:
                filename = f"{row}.webm"

            # Set video
            cap = cv2.VideoCapture(f"{directory}/{filename}")

            # Choose which intervals are useful, given that the csv has the useless seconds
            frames_per_second = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            useful_seconds = Editor._get_intervals(seconds[row - begin], frames_per_second, frame_count)

            # The video is useless
            if len(useful_seconds[0]) == 0:
                continue

            print(useful_seconds)

            # For the interval of seconds, get the frames
            for interval in useful_seconds:

                # Set the interval
                start = interval[0]
                end = interval[1]

                num_frame = 0

                # Get half of the frames in that range
                first = int(start * frames_per_second)
                last = int(end * frames_per_second)
                current = first
                n = 2

                # Get the frames
                cap.set(cv2.CAP_PROP_POS_FRAMES, current)
                success, image = cap.read()
                while success and current <= last:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, current)
                    success, frame = cap.read()

                    # Resize images to 1920 x 1080
                    width, height, _ = frame.shape
                    if width == 2160 and height == 3840:
                        pass
                        # frame = cv2.resize(frame, (1920, 1080))

                    # Save file, row (from the original csv), frame and id from YouTube link
                    output_name = f'./images/{row}-{num_frame}-{video_id}'
                    # cv2.imwrite(f"{output_name}.png", frame)

                    # Get the next frames jumping between n frames
                    current += n
                    num_frame += 1

            print(f"Done video: {row}")

    @staticmethod
    def _get_intervals(seconds: list, fps: int, fc: int) -> list:
        """
        Returns a list with intervals of the useful seconds given a list
        of intervals with useless seconds.
        fps: frames per seconds
        fp: total amount of frames in the video
        """
        # The video was not useful
        if seconds[0][0] == 1 and seconds[0][1] == 0:
            return [[]]

        # All the frames in the video are useful
        elif seconds[0][0] == 0 and seconds[0][1] == 0:
            start = 0
            end = int(fc / fps) - 1
            return [[start, end]]

        # Get the useful intervals for the other ranges
        intervals = []
        total_seconds = int(fc // fps)

        # If the first useless interval takes the beginning of the video, then
        # take the end of that fragment and use it as the beginning of the
        # intervals, otherwise take 0
        if seconds[0][0] == 0:
            begin = seconds[0][1]
            b = 1
        else:
            begin = 0
            b = 0

        # Fill the interval's middle
        for gap in seconds[b:]:
            end = gap[0]
            intervals.append([begin, end])
            begin = gap[1]

        # Check if the last useless second was the last second on the video
        # if so, do not add anymore. If not, add the last interval
        if seconds[-1][1] == total_seconds:
            return intervals

        intervals.append([begin, total_seconds])
        return intervals

    @staticmethod
    def from_webm_to_mp4() -> None:
        """
        Using ffmpeg convert a video from webm to mp4 and save them in the
        raw_videos folder
        """
        # Where it gets the video and where it is saved
        input_directory = "./convert_videos"
        output_directory = "./raw_videos"

        # Iterate over each video in the folder
        for video in os.listdir(input_directory):
            filename = os.fsdecode(video)

            # The name does not change, it keeps the number of its row in the
            # original csv file
            row = filename[:-5]

            # Change its extension to mp4
            input_stream = f"{input_directory}/{filename}"
            output_name = f"{output_directory}/{row}.mp4"

            stream = ffmpeg.input(input_stream)
            stream = ffmpeg.output(stream, output_name)
            ffmpeg.run(stream)
