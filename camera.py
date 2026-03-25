#!/usr/bin/env python3
from cv2 import VideoCapture, imencode, CAP_PROP_AUTO_EXPOSURE
from linuxpy.video.device import iter_video_capture_devices
from loguru import logger

def takePhotoOnDevice(priorities):
    cameraIndex = find_camera_index(priorities)
    camera = VideoCapture(cameraIndex)
    camera.set(CAP_PROP_AUTO_EXPOSURE, 3)
    for _ in range(5):  # discard frames to let auto-exposure settle
        camera.read()
    result, image = camera.read()
    camera.release()
    if not result:
        logger.warning("Failed to capture photo from camera index {}", cameraIndex)
        return None
    return imencode('.png', image)[1]


def find_camera_index(priorities):
    if len(priorities) == 0:
        logger.warning("No matching camera found for priorities, falling back to device 0")
        return 0
    iterator = iter_video_capture_devices()
    for c in iterator:
        c.open()
        name = c.info.card
        c.close()
        if priorities[0] in name:
            return c.index

    return find_camera_index(priorities[1:])
