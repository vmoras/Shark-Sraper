import cv2
import ffmpeg
import os
from collections import Counter
import time
import imagehash
import imutils
import numpy
import numpy as np
from PIL import Image
import pandas as pd
from imutils.video import FileVideoStream
from imutils.video import FPS


class Editor:
    @staticmethod
    def get_images() -> None:
        """
        Creates threads where each one will download an interval of frames
        from a video
        """
        # In which folder are the videos to be edited and what is the range of their
        # index
        directory = "./videos_youtube"
        num_videos = len(os.listdir(directory))
        first, last = 14, num_videos
        last = 20

        Editor._extract_frames_range((first, last), directory)

    @staticmethod
    def _extract_frames_range(slicing: tuple, directory: str) -> None:
        """
        Saves the frames from a given range of seconds. The input are the seconds to remove,
        in other words, the intervals between each range are the frames to obtain.

        OpenCV is not the best at getting the n-th frame (if the file was too big, it collapsed),
        and decord can not handle webm files. So imutils was used.
        """
        # Set directory and Data Frame with the info
        df = pd.read_csv("videos_tiburones.csv", index_col=0)

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

        # For each video in the given range find it and get its frames
        videos_id = df.loc[begin: end, "URL"].tolist()

        for row in range(begin, end + 1):
            print(f"Editing video: {row}")
            video_id = videos_id[row - begin][32:]
            useless_seconds = seconds[row - begin]

            # The video is not useful
            if useless_seconds[0][0] == 1 and useless_seconds[0][1] == 0:
                continue

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
            useful_seconds = Editor._get_intervals(useless_seconds, frames_per_second, frame_count)

            # Get the black border (if they have one) to remove it
            first_frame = useful_seconds[0][0]
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(first_frame * frames_per_second))
            _, image = cap.read()
            y, h, x, w = Editor._get_black_border(image)

            # Sometimes there is a weird bug, and the border grab but in a weird way
            if h < y or w < x:
                print("THERE IS A PROBLEM WITH THE BLACK BORDER, CHECK VIDEO")
                continue

            # Keep track of how many images have been saved
            num_frame = 0
            total_frames = int(5 * frames_per_second * 5)

            # Getting the n-th frame is expensive, so it will iterate over all the frames
            # and read them, but it will only save those in the interval
            video = FileVideoStream(f"{directory}/{filename}", queue_size=1000).start()
            time.sleep(1)
            fps = FPS().start()
            current = 0

            # For each interval of seconds, get the frames
            print(f"Intervals: {useful_seconds}")
            frame = None
            for start, end in useful_seconds:

                # Get the number of the first and last frame and
                # the number of the frame in the middle of that range
                first = int(start * frames_per_second)
                last = int(end * frames_per_second)
                middle = (last + first) // 2

                # Iterate until it gets to the first frame
                while current < first:
                    frame = video.read()
                    fps.update()
                    current += 1

                # Save the first frame, for debugging
                output_name = f'{row}-{current}-{video_id}'
                cv2.imwrite(f"./images_debug/{output_name}.png", frame)

                # Save all the frames in the interval
                while current <= last:
                    frame = video.read()

                    # The video has a black border somewhere, remove it
                    if y != 0 or x != 0:
                        frame = frame[y:y + h, x:x + w]

                    # Save frame
                    output_name = f'{row}-{current}-{video_id}'
                    cv2.imwrite(f"./images_raw/{output_name}.png", frame)

                    # Save middle frame
                    if current == middle:
                        output_name = f'{row}-{current}-{video_id}'
                        cv2.imwrite(f"./images_label/{output_name}.png", frame)

                    fps.update()
                    current += 1
                    num_frame += 1

                # Save last frame for labeling and debugging
                output_name = f'{row}-{current - 1}-{video_id}'
                cv2.imwrite(f"./images_label/{output_name}.png", frame)
                cv2.imwrite(f"./images_debug/{output_name}.png", frame)

            print(f"Done video   : {row}. {num_frame}/{total_frames}")
            print("-----------------------------------------------")

    @staticmethod
    def _get_intervals(seconds: list, fps: int, fc: int) -> list[[int, int]]:
        """
        Returns a list with 5 intervals each one of 5 seconds of the useful
        seconds given a list of intervals with useless seconds. First
        it gets the useful seconds, then makes intervals of 5 seconds
        and finally takes the first, first quarter, middle, third quarter
        and last interval. It allows us to get different intervals with
        different info.

        fps: frames per seconds
        fp: total amount of frames in the video
        """
        # Get the useful seconds
        intervals = Editor._get_big_intervals(seconds, fps, fc)

        ranges = [[[], []] for _ in range(5)]

        # There is one big interval, so the calculations are easier, there
        # is no need to get one by one interval of 5 seconds
        if len(intervals) == 1:
            start = intervals[0][0]
            end = intervals[0][1]

            ranges[0][0], ranges[0][1] = start, start + 5

            ranges[-1][0], ranges[-1][1] = end - 5, end

            middle = (start + end) // 2
            ranges[2][0], ranges[2][1] = middle, middle + 5

            first_quarter = (start + middle) // 2
            ranges[1][0], ranges[1][1] = first_quarter, first_quarter + 5

            third_quarter = (middle + end) // 2
            ranges[3][0], ranges[3][1] = third_quarter, third_quarter + 5

            return ranges

        # The useful seconds are not connected, in other words, they are in
        # different intervals. So, get all the 5 seconds intervals in those
        # sections and then get the 5 intervals.
        else:
            all_ranges = []
            for interval in intervals:
                start = interval[0]
                end = interval[1]

                i = start
                j = start + 5

                while j <= end:
                    all_ranges.append([i, j])
                    i, j = j, j+5

            # First and last
            ranges[0], ranges[-1] = all_ranges[0], all_ranges[-1]

            middle = len(all_ranges) // 2
            ranges[2] = all_ranges[middle]

            first_quarter = middle // 2
            ranges[1] = all_ranges[first_quarter]

            third_quarter = first_quarter + middle
            ranges[3] = all_ranges[third_quarter]

            return ranges

    @staticmethod
    def _get_big_intervals(seconds: list, fps: int, fc: int) -> list[[int, int]]:
        """
        Returns each useful interval given a list of useless intervals. It uses
        a margin of error of 0.5 seconds.
        """
        # All the frames in the video are useful
        if seconds[0][0] == 0 and seconds[0][1] == 0:
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
            begin = seconds[0][1] + 0.5
            b = 1
        else:
            begin = 0
            b = 0

        # Fill the interval's middle
        for gap in seconds[b:]:
            end = gap[0] - 0.5
            intervals.append([begin, end])
            begin = gap[1] + 0.5

        # Check if the last useless second was the last second on the video
        # if so, do not add anymore. If not, add the last interval
        if seconds[-1][1] == total_seconds:
            return intervals

        intervals.append([begin, total_seconds])

        # Fix the last value
        intervals[-1][-1] = intervals[-1][-1] - 0.5

        return intervals

    @staticmethod
    def from_webm_to_mp4() -> None:
        """
        Using ffmpeg convert a video from webm to mp4 and save them in the
        raw_videos folder
        """
        # Where it gets the video and where it is saved
        input_directory = "./videos_youtube"
        output_directory = "./videos_youtube"

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

    @staticmethod
    def _get_black_border(img: numpy.ndarray) -> tuple[int, int, int, int]:
        """
        Returns the coordinates for the main image, eliminating
        any black border (if it has one).

        The return values are:
        y: from top to bottom, the pixel where the image starts
        h: height of the image
        x: from left to right, the pixel where the image starts
        w: width of the image
        """
        # Make the image grey, so it is easier to find the black
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # TODO: understand how this works
        _, thresh = cv2.threshold(gray_img, 5, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
        morph = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel=kernel)
        contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnt = contours[0]

        # Make a rectangle around the points, so it surrounds the image
        x, y, w, h = cv2.boundingRect(cnt)

        return y, h, x, w

    @staticmethod
    def get_mask(file: str) -> None:
        """
        Returns a mask with only 1 channel. It overwrites the
        input file
        """
        # read input image
        img = cv2.imread(file)

        # Convert BGR to HSV
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Define range of white color in HSV
        lower_white = np.array([0, 0, 0])
        upper_white = np.array([0, 0, 255])

        # Create a mask. Threshold the HSV image to get only white color
        mask = cv2.inRange(hsv, lower_white, upper_white)

        # Bitwise-AND mask and original image
        result = cv2.bitwise_and(img, img, mask=mask)
        cv2.imwrite(file, result)

    @staticmethod
    def _remove_watermark():
        """
        TODO: finish
        """
        small_image = cv2.imread("border.png", 0)
        prohibited_files = ["303", "320", "323", "363", "367"]

        for image in os.listdir("./images_croped"):
            filename = os.fsdecode(image)

            if any(filename[:3] == name for name in prohibited_files):
                continue
            large_image = cv2.imread(f'./images_croped/{filename}')

            height = large_image.shape[0]
            width = large_image.shape[1]

            search_height = height // 2 + (height // 4)
            search_width = width // 2 + (width // 4)

            middle_right = large_image[height // 2: height, width // 2: width]
            height = middle_right.shape[0]
            width = middle_right.shape[1]

            search = middle_right[height // 2: height, width // 2: width]

            template = cv2.cvtColor(search, cv2.COLOR_BGR2GRAY)
            template = cv2.Canny(template, 50, 200)

            max_value = 0
            best_position = 0
            best_scale = 0

            for scale in np.linspace(0.2, 1.0, 20)[::-1]:

                new_width = int(small_image.shape[1] * scale)
                resized = imutils.resize(small_image, new_width)

                result = cv2.matchTemplate(resized, template, cv2.TM_SQDIFF_NORMED)

                value, _, position, _ = cv2.minMaxLoc(result)

                if value < max_value:
                    max_value = value
                    best_position = position
                    best_scale = new_width

            if best_scale == 0:
                continue

            best_scale += 1

            if best_scale != 1:
                best_img = imutils.resize(small_image, best_scale)

            else:
                best_img = small_image

            m = max_value // 1000000
            print(filename, max_value, m, best_scale)

            MPx, MPy = best_position
            MPx += search_width
            MPy += search_height
            trows, tcols = best_img.shape[:2]

            change = large_image[MPy: MPy + trows, MPx:MPx + tcols]

            mask = cv2.imread("./masks/other_mask.png", 0)
            mask = imutils.resize(mask, best_scale)

            dst = cv2.inpaint(change, mask, 3, cv2.INPAINT_TELEA)

            large_image[MPy: MPy + trows, MPx:MPx + tcols] = dst
            cv2.imwrite(f"./images_fixed/{filename}", large_image)

    @staticmethod
    def compare_videos():
        """
        TODO: finish
        """
        yt_path = "y_cropped.webm"
        i_path = "./IVideos/32.mp4"

        i_vid = cv2.VideoCapture(i_path)
        y_vid = cv2.VideoCapture(yt_path)

        i_frames = int(i_vid.get(cv2.CAP_PROP_FRAME_COUNT))
        y_frames = int(y_vid.get(cv2.CAP_PROP_FRAME_COUNT))

        # Get the new width of the frame from YouTube using a ratio of 9:16
        y_vid.set(cv2.CAP_PROP_POS_FRAMES, 0)
        _, y_frame = y_vid.read()
        width_yt = y_vid.get(cv2.CAP_PROP_FRAME_WIDTH) // 2
        height_yt = y_vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
        new_width = (9 / 16 * height_yt) // 2

        # Resize the frame from YouTube
        left = int(width_yt - new_width)
        right = int(width_yt + new_width)

        mini = 100
        c, p = 0, 0

        colors = []

        yt_frames = []
        for y in range(0, y_frames, 145):
            y_vid.set(cv2.CAP_PROP_POS_FRAMES, y)
            _, y_frame = y_vid.read()
            yt_frames.append(y_frame)

        in_frames = []
        for i in range(0, i_frames, 145):
            i_vid.set(cv2.CAP_PROP_POS_FRAMES, i)
            _, i_frame = i_vid.read()
            in_frames.append(i_frame)

        for i in in_frames:
            for y in yt_frames:

                y = y[150:, left-120:right-150]
                # y_frame = y_frame[:, left-120:right-150]

                i_img = Image.fromarray(numpy.uint8(i))
                y_img = Image.fromarray(numpy.uint8(y))

                start_time = time.time()
                i_color = imagehash.colorhash(i_img)
                y_color = imagehash.colorhash(y_img)
                c += time.time() - start_time

                start_time = time.time()
                i_hash = imagehash.phash(i_img)
                y_hash = imagehash.phash(y_img)
                p += time.time() - start_time

                color = i_color - y_color
                ahash = i_hash - y_hash

                colors.append(color)

                if color < 5 & ahash < mini:
                    mini = i_hash - y_hash
                    y_img.show(title=f"YouTube,{y}")
                    i_img.show(title=f"Instagram,{i}")

        print(c, p, mini)
        print(Counter(colors))

