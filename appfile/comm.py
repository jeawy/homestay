#！ -*- coding:utf-8 -*-
import os
import pdb 
from common.fileupload import FileUpload
from appfile.models import Attachment
from property.code import *
from common.logutils import getLogger
from django.conf import settings

logger = getLogger(True, 'appfile', False)


class AppFileMgr(object):
    """
    系统文件上传下载管理
    """
    @classmethod
    def filelist(cls, apptype, appid = None):
        """
        apptype: app类型
        appid：app id
        返回： 文件列表
        """
        kwargs = {}
        if appid:
            kwargs['app_id'] = appid 
        kwargs['apptype'] = apptype
        attacnments = Attachment.objects.filter(**kwargs)
        return attacnments

    @classmethod
    def upload(cls, fileobj, filepath, filename, apptype, appid):
        """
        上传附件
        :param fileobj: 文件对象
        :param apptype: app类型
        :param appid: app id 
        :return:result = {
            "status": SUCCESS,
            "msg":""
            }
        """
        result = {
            "status": SUCCESS,
            "msg":""
            }
        logger.debug("write to database")
        attachfile = Attachment.objects.create(app_id = appid, 
                                apptype = apptype,
                                filename = filename,
                                filepath = filepath)
        if apptype not in attachfile.filetype_list:
            attachfile.delete()
            result['status'] = APPFILE_TYPE_ERROR
            result['msg'] = "未识别的文件类型"
        else: 
            logger.debug("start to upload file")
            FileUpload.upload(fileobj, filepath, filename)
            result['msg'] = attachfile.id
        return result
         
    @classmethod
    def removefile(cls, fileid = None, appid = None, apptype = None):
        """
        删除附件
        :param fileid: 指定删除单个文件
        :param appid 和 apptype: 指定删除某个app下的某个实例的全部附件
                                 这两个参数被优先考虑
        :return:
        """
        result = {
            "status": SUCCESS,
            "msg":""
            }
        attaches = []
        if appid and apptype:
            attaches = Attachment.objects.filter( apptype = apptype, 
                                 app_id = appid) 
        elif fileid:
            attaches = Attachment.objects.filter( id = fileid )
            
        for attach in attaches:
            filefullpath = os.path.join(attach.filepath, attach.filename)
            if os.path.isfile(filefullpath):
                logger.warning("{0} has been deleted".format(filefullpath))
                os.remove(filefullpath)
        
        if attaches:
            attaches.delete() 
        return result


                    
if __name__ == "__main__":
    # 删除
    fileslist = AppFileMgr.removefile(apptype = 1, appid=1  )

