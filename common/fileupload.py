#！ -*- coding:utf-8 -*-
import os
import pdb
from django.conf import settings
from PIL import Image


class FileUpload(object):
    @staticmethod
    def upload(f, path, name, optimize = False):
        """
        文件上传
        path: 目标存储路径
        name:文件名称
        optimize 仅对图片优化起作用,压缩图片
        """
        path = os.path.join(settings.FILEPATH, path)
        destination = os.path.join(path, name)
        if not os.path.isdir(path):
            os.makedirs(path) 
        with open(destination, 'wb+') as destinationfile:
            for chuck in f.chunks():
                destinationfile.write(chuck) 
        if optimize:
            if os.path.getsize(destination.name) > settings.FILE_MAX_SIZE : 
                image = Image.open(destination.name) 
                image.save(destination.name,quality=settings.FILE_COMPRESSION_RIO,optimize=True)
        return destination
        
    
    @staticmethod
    def allow_image_type(name):
        """
        检测系统中运行上传的图片文件格式
        """
        if not (name.endswith('.png') or name.endswith('.jpeg') or \
            name.endswith('.jpg') ):
            return False
        else:
            return True
        