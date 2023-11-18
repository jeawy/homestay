import pdb
import os
import shutil
import time
import subprocess
import cv2
from django.utils import timezone

from property import settings
from common.logutils import getLogger
logger = getLogger(True, 'convert', False)

"""
例子：
video_path = '/images/5.mp4'
frame_save_path = os.path.join(settings.FILEPATH, 'framevideo')
frame_path = video2frame(video_path, frame_save_path)
print(frame_path)
images = "D:\\image\\5.png", "D:\\image\\168.png"
replace_frames(images, frame_path)
pic_video(frame_path, video_path)
shutil.rmtree(frame_path)
"""

def video2frame(video_path, frame_save_path, code):
    """
    将视频逐帧读取写入图片
    :param video_path: 视频存放相对路径 "/images/5.mp4"
    :param frame_save_path:　视频帧保存路径
    'D:\\Program Files\\pyworkspace\\property\\images\\frame'
    :return: frame_path: 视频帧保存详情地址
    'D:\\Program Files\\pyworkspace\\property\\images\\frame\\5v20191128164807'
    """
    result = {}
    video = video_path.replace('/images/', '')
    video_name = video[:-4]
    time_tag = timezone.now().strftime("%Y%m%d%H%M%S")
    file_name = video_name + "v" + time_tag
    frame_path = os.path.join(frame_save_path, code, file_name)
    relative_path = os.path.join(os.path.join(settings.IMAGEROOTPATH, 'framevideo'),
                              code, file_name)
    if not os.path.exists(frame_path):
        os.makedirs(frame_path)

    each_video_full_path = os.path.join(settings.FILEPATH, video)

    cap = cv2.VideoCapture(each_video_full_path)
    frame_count = 1
    if cap.isOpened():
        success = True
    else:
        success = False
        print("读取失败!")

    while (success):
        success, frame = cap.read()
        if success:
            cv2.imwrite(os.path.join(frame_path, str(frame_count) + '.png'), frame)
            frame_count += 1

    cap.release()
    result['file_name'] = file_name
    result['frame_path'] = frame_path
    result['relative_path'] = relative_path
    return result


def pic_video(frame_path, video_path, file_name):
    """
    图片合成视频
    :param frame_path: 视频帧保存详情地址
    'D:\\Program Files\\pyworkspace\\property\\images\\frame\\5v20191128164807'
    :param video_path: 视频存放相对路径 "/images/5.mp4"
    :param file_name: 文件名称 "5v20191128164807"
    :return: file_path "新视频的导出地址 "D:\\videos\\aaaa.mp4"
    """
    file_path = frame_path + ".mp4"
    frame_video_path = os.path.join(settings.IMAGEROOTPATH, 'framevideo',
                                    file_name + ".mp4")
    video_path = video_full_path(video_path)
    # 获取帧率
    result = vedio_info(video_path)
    fps = result['fps']
    size = result['size']
    result['frame_video_path'] = frame_video_path
    # fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
    # fourcc = cv2.VideoWriter_fourcc('H','2','6','4')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(file_path, fourcc, fps, size)
    for i in range(1, int(result['frameCount'])+1):
        item = os.path.join(frame_path, str(i) + '.png')
        img = cv2.imread(item)
        video.write(img)

    video.release()
    return result

def vedio_info(video_path):
    """
    获取视频的基本信息：
    fps：帧率
    frameCount：总帧数
    size：大小
    :param video_path: 视频详情地址 "D:\\videos\\cccc.mp4"
    :return: result
    """
    result = {}
    video = cv2.VideoCapture(video_path)

    # Find OpenCV version
    (major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')

    if int(major_ver)  < 3 :
        fps = video.get(cv2.cv.CV_CAP_PROP_FPS)
    else:
        fps = video.get(cv2.CAP_PROP_FPS)

    size = (int(video.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(video.get(cv2.CAP_PROP_FRAME_HEIGHT)))

    frameCount = video.get(cv2.CAP_PROP_FRAME_COUNT)

    video.release()
    result['fps'] = fps
    result['size'] = size
    result['frameCount'] = frameCount
    return result

def replace_frames(image_list, frame_path):
    """
    将要替换视频指定帧的一组图片
    :param images: "D:\\image\\5.png","D:\\image\\168.png"
    [{'frame': 158, 'name': 'asset_id_3802_time_20191128111010448427.png'}]
    :param frame_path: 视频帧保存详情地址
    'D:\\Program Files\\pyworkspace\\property\\images\\frame\\5v20191128164807'
    :return:
    """
    image_path = os.path.join(settings.FILEPATH, 'image')
    if not os.path.exists(frame_path):
        os.makedirs(frame_path)
    for image in image_list:
        # 复制替换的文件
        shutil.copy(os.path.join(image_path, image['name']), frame_path)
        frame_img = os.path.join(frame_path, str(image['frame']) + ".png")
        replace_img = os.path.join(frame_path, str(image['name']))
        # 要替换的文件存在，并且
        # replace_img和frame_img文件名不相等，没有被覆盖
        if os.path.exists(frame_img) and replace_img != frame_img:
            os.remove(frame_img)
        # 重命名替换的文件
        os.rename(replace_img, frame_img)

def video_full_path(video_path):
    """
    获取视频详情地址
    :param video_path:视频存放相对路径 "/images/5.mp4"
    :return: video_full_path：
    """
    video = video_path.replace('/images/', '')
    video_full_path = os.path.join(settings.FILEPATH, video)
    return video_full_path


def convert_mp4(input_mp4, output_mp4):
    """
    ffmpeg -i 5v20191129113058.mp4 -vcodec h264 output.mp4
    input_mp4 输入文件的相对路径，相对项目根目录的路径
    output_mp4 输出文件的相对路径，相对项目根目录的路径
    转换成功返回True
    否则返回False
    """
    abs_input_mp4 = os.path.join(settings.BASE_DIR, input_mp4)
    abs_output_mp4 = os.path.join(settings.BASE_DIR, output_mp4)
    if os.path.isfile(abs_input_mp4):
        if os.path.isfile(abs_output_mp4):
            os.path.remove(abs_output_mp4)
        start = time.time()
        result = subprocess.run(['ffmpeg', '-i', abs_input_mp4, '-vcodec', 'h264', abs_output_mp4], 
                               stdout=subprocess.PIPE)
        end = time.time()
        logger.debug("convert mp4 used: {0}".format(str(end-start)))
        if result.returncode == 0:
            return True 
        else:
            return False
    else:
        return False  
