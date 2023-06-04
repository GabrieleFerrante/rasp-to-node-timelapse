import os
import sys
import requests as rq
from picamera import PiCamera
from time import sleep
from io import BytesIO
from logzero import logger, logfile


class Timelapse:
    def __init__(self) -> None:
        self.resolution = [1024, 576]
        self.flipped = ("--flipped" in sys.argv) or ("-f" in sys.argv)
        self.camera_warmup_time = 5  # Seconds
        self.wait_time = 15  # Seconds
        self.image_directory = os.path.join(".", "images")
        self.post_url = "http://192.168.1.15:5000/timelapse"
        self.log_file = os.path.join(".", "events.log")
        self.iterations = 10
        self.infinite = True

        for e in sys.argv:
            if "--width=" in e:
                self.resolution[0] = int(e.replace("--width=", ""))
            if "--height=" in e:
                self.resolution[1] = int(e.replace("--height=", ""))
            if "--warmup=" in e:
                self.camera_warmup_time = float(e.replace("--warmup=", ""))
            if "--wait=" in e:
                self.wait_time = float(e.replace("--wait=", ""))
            if "--url=" in e:
                self.post_url = e.replace("--url=", "http://")
            if "--path=" in e:
                self.image_directory = os.path.join(
                    ".", e.replace("--path=", "").replace("./", "").strip('"')
                )
            if "--finite" in e:
                self.infinite = False
            if "--iterations=" in e:
                self.iterations = int(e.replace("--iterations=", ""))

    def start(self):
        if not os.path.exists(self.image_directory):
            os.mkdir(self.image_directory)

        if not os.path.exists(self.log_file):
            with open(self.log_file, "w"):
                pass
        logfile(self.log_file)

        logger.info("-" * 15)

        with PiCamera() as camera:
            camera.resolution = tuple(self.resolution)
            camera.rotation = 180 if self.flipped else 0
            camera.start_preview()
            logger.info(f"Waiting for camera warm up time: {self.camera_warmup_time}s")
            sleep(self.camera_warmup_time)

            counter = 0

            while counter < self.iterations or self.infinite:
                image_name = f"{counter}.png"

                camera.capture(os.path.join(self.image_directory, image_name))
                logger.info(f"Caught image {counter}")

                try:
                    file = open(os.path.join(self.image_directory, image_name), "rb")
                    files = {"file": (image_name, file, "image/x-png")}
                    response = rq.post(self.post_url, files=files)
                    logger.info(f"Sent image {counter}")
                    logger.info(f"Response status code: {response.status_code}")
                except Exception as e:
                    logger.info(f"Could not POST: {e}")
                finally:
                    file.close()
                    if os.path.exists(os.path.join(self.image_directory, image_name)):
                        os.remove(os.path.join(self.image_directory, image_name))

                sleep(self.wait_time)
                counter += 1


if __name__ == "__main__":
    Timelapse().start()