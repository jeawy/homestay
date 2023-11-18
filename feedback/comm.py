import json
import pdb
import time
from feedback.models import Feedback, FdkImgs
from property.code import SUCCESS, ERROR


def single_feedback(id):
    """
    意见反馈详情
    """
    content = {
        'status':SUCCESS
    }
    try:
        feedback = Feedback.objects.get(id=id)
        notice_content = {}
        notice_content['id'] = feedback.id
        notice_content['content'] = feedback.content
        notice_content['contact'] = feedback.contact
        if feedback.score:
            notice_content['score'] = feedback.score
        else:
            notice_content['score'] = ''
        notice_content['read'] = feedback.read
        notice_content['status'] = feedback.status
        notice_content['device'] = feedback.device
        notice_content['os'] = feedback.os
        notice_content['result'] = feedback.result
        if feedback.date:
            notice_content['date'] = time.mktime(feedback.date.timetuple())
        else:
            notice_content['date'] = ''
        imgs = FdkImgs.objects.filter(feedback=feedback)
        img_list = []
        if imgs:
            for img in imgs:
                img_dic = {}
                img_dic['filename'] = img.filename
                img_dic['filepath'] = img.filepath
                img_list.append(img_dic)
        notice_content['images'] = img_list
        content['status'] = SUCCESS
        content['msg'] = notice_content
    except Feedback.DoesNotExist:
        content['status'] = ERROR
        content['msg'] = '反馈不存在'
    return content