#！ -*- coding:utf-8 -*-
import os
from property import settings
from datetime import datetime


class Code(object):
    @staticmethod
    def get(building_code, room_code, request_type):
        """
        各类请求的编码规则
        :param building_code:
        :param room_code:
        :param request_type:
        :return: 返回规则字符串
        """
        datestr = datetime.now().strftime('%Y%m%d%H%M%S%f')
        if request_type == 'repair':
            request_type = 'R'
        elif request_type == 'parking':
            request_type = 'P'
        elif request_type == 'annoucement':
            request_type = 'A'
        return building_code+room_code+request_type+datestr