import cv2
import os
import pdb
import time
from django.conf import settings


def get_pic(video, frame): 
    #在这里把后缀接上
    video_path = os.path.join(settings.VIDEO_PATH , video) 
    print(video_path)
    if not os.path.isfile(video_path):
        return -1, "视频文件不存在", ''
    #输出图片到当前目录vedio文件夹下
    start = time.time()
    outPutDirName = settings.VIDEO_IMAGE_PATH
    if not os.path.exists(settings.VIDEO_IMAGE_PATH):
        #如果文件目录不存在则创建目录
        os.makedirs(settings.VIDEO_IMAGE_PATH) 
    camera = cv2.VideoCapture(video_path)
    fps = camera.get(cv2.CAP_PROP_FPS) 
     
    camera.set(cv2.CAP_PROP_POS_FRAMES, frame)
    res, image = camera.read() 
    outfile = os.path.join(outPutDirName, str(frame)+'.jpg')
    cv2.imwrite(outfile, image)
    end = time.time()

    camera.release() 
    return 0, fps, os.path.join(settings.PROJECT_PATH, str(frame)+'.jpg')