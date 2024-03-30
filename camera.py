#!/usr/bin/env python3
from cv2 import VideoCapture, imencode
from linuxpy.video.device import iter_video_capture_devices

def takePhotoOnDevice(priorities):
    cameraIndex = find_camera_index(priorities)
    camera = VideoCapture(cameraIndex)
    result, image = camera.read()
    camera.release()
    camera2 = VideoCapture(cameraIndex)
    result, image2 = camera2.read()
    camera2.release()
    if result:
        data1 = imencode('.png', image)[1]
        data2 = imencode('.png', image2)[1]
        if (len(data1) > len(data2)):
            return data1
        else:
            return data2
    return None


def find_camera_index(priorities):
    if len(priorities) == 0:
        return 0
    iterator = iter_video_capture_devices()
    for c in iterator:
        c.open()
        name = c.info.card
        c.close()
        if priorities[0] in name:
            return c.index

    return find_camera_index(priorities[1:])
