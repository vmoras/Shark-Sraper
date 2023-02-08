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
        first = 0
        last = num_videos
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
        Saves the frames from a given range of seconds
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
        seconds_list = [list(second.split(",")) for second in seconds_videos]

        seconds = []
        for seconds_video in seconds_list:
            ranges_video = [tuple(map(int, interval.split(":"))) for interval in seconds_video]
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

            # For the interval of seconds, get the frames
            for interval in seconds[row - begin]:
                start = interval[0]
                end = interval[1]
                num_frame = 0

                # Get half of the frames in that range
                frames_per_second = cap.get(cv2.CAP_PROP_FPS)
                first = int(start * frames_per_second)
                last = int(end * frames_per_second)
                current = first
                n = 10

                cap.set(cv2.CAP_PROP_POS_FRAMES, current)
                success, image = cap.read()

                while success and current <= last:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, current)
                    success, frame = cap.read()

                    # Resize images to 1920 x 1080
                    width, height, _ = frame.shape
                    if width == 2160 and height == 3840:
                        frame = cv2.resize(frame, (1920, 1080))

                    # Save file, row (from the original csv), frame and id from YouTube link
                    output_name = f'./images/{row}-{num_frame}-{video_id}'
                    cv2.imwrite(f"{output_name}.png", frame)

                    # Get the next frames jumping between n frames
                    current += n
                    num_frame += 1

            print(f"Done video: {row}")

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
