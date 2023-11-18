# ！ -*- coding:utf-8 -*-
import re
import pdb
import os
from PIL import Image
import platform
import uuid
import qrcode
from datetime import datetime
from django.utils import timezone
from django.conf import settings 
from pypinyin import pinyin, Style
from math import sin, cos, sqrt, atan2, radians

def getDistance(startpoint, endpoint):
    """
    获得两点直接的距离
    """
    # approximate radius of earth in km
    R = 6373.0 
    """
    lat1 = radians(52.2296756)
    lon1 = radians(21.0122287)
    lat2 = radians(52.406374)
    lon2 = radians(16.9251681)
    """
    lat1 = radians(startpoint['lat'])
    lon1 = radians(startpoint['lon'])
    lat2 = radians(endpoint['lat'])
    lon2 = radians(endpoint['lon'])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c

    print("Result:", distance) 
    return distance
    

def getStrAllAplha(hanzi):
    """
    获取所有汉字的拼音首字母
    输入：你好在哪来
    输出：NHZNL
    """
    pinyin('中心', style=Style.FIRST_LETTER)
    # pinyin('中心', style=Style.FIRST_LETTER)  # 设置拼音风格
    # [['z'], ['x']]
    return pinyin(hanzi, style=Style.FIRST_LETTER) # pinyin().get_initial(str, delimiter="").upper()

def getStrFirstAplha(hanzi):
    """
    获取第一个汉字的拼音首字母
    输入：你好在哪来
    输出：N
    """
    hanzi=getStrAllAplha(hanzi) 
    hanzi=hanzi[0][0]
    return hanzi.upper()


def verify_email(email):
    """验证邮箱格式
    合法返回 True，否则返回False
    """

    EMAIL_REGEX = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
    if EMAIL_REGEX.match(email):
        return True
    else:
        return False


def create_logo_qrcode(url):
    # 生成带logo的二维码
    qrcodepath = os.path.join(settings.FILEPATH, 'qrcode')
    if not os.path.isdir(qrcodepath):
        os.makedirs(qrcodepath)
    qrcodefile = os.path.join(qrcodepath, str(uuid.uuid4())+".png")
    
    qr = qrcode.QRCode(version=5,error_correction=qrcode.constants.ERROR_CORRECT_H,box_size=8,border=4)
    qr.add_data(url)
    qr.make(fit=True) 
    img = qr.make_image()
    img = img.convert("RGBA")

    logo = os.path.join( settings.BASE_DIR, 'staticend', 'img', 'logo.png')
    icon = Image.open(logo)

    img_w,img_h = img.size
    factor = 4
    size_w = int(img_w / factor)
    size_h = int(img_h / factor)

    icon_w,icon_h = icon.size
    if icon_w >size_w:
        icon_w = size_w
    if icon_h > size_h:
        icon_h = size_h
    icon = icon.resize((icon_w,icon_h),Image.ANTIALIAS)

    w = int((img_w - icon_w)/2)
    h = int((img_h - icon_h)/2)
    icon = icon.convert("RGBA")
    img.paste(icon,(w,h),icon)
    with open(qrcodefile, 'wb') as f:
        img.save(f)
    
    return qrcodefile.replace(settings.FILEPATH, "")

def get_qrcode(url):
    """
    生成二维码
    并返回生成的二维码路径
    """
    img = qrcode.make(url)
    qrcodepath = os.path.join(settings.FILEPATH, 'qrcode')
    if not os.path.isdir(qrcodepath):
        os.makedirs(qrcodepath)
    qrcodefile = os.path.join(qrcodepath, str(uuid.uuid4())+".png")
    with open(qrcodefile, 'wb') as f:
        img.save(f)
    return qrcodefile.replace(settings.LOG_HOME, "")


def verify_phone(phone):
    """验证电话格式
    合法返回 True，否则返回False
    """
    PHONE_REGEX = re.compile(r"^((13[0-9])|(14[0-9])|(15[0-9])|(17[0-9])|(19[0-9])|(18[0-9]))\d{8}$")
    if PHONE_REGEX.match(phone):
        return True
    else:
        return False


def list_files(startpath):
    # list-directory-tree-structure
    filesstr = ""
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        # print('{}{}/'.format(indent, os.path.basename(root)))
        filesstr = filesstr + '{}{}/'.format(indent, os.path.basename(root)) + '\r\n'
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            filesstr = filesstr + '{}{}'.format(subindent, f) + '\r\n'

    return filesstr


def format_all_dates(date_str):
    """
    格式化：yyyy.mm.dd
           yyyy/mm/dd
           yyyy-mm-dd
           yyyymmdd
           yyyy年mm月dd日
    为日期
    格式错误时，返回None
    成功时，返回日期
    """
    date = None
    date_str = str(date_str)
    try:
        if date_str: 
            if '/' in date_str:
                date = datetime.strptime(date_str, "%Y/%m/%d").date()
            elif '-' in date_str:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
            elif '.' in date_str:
                date = datetime.strptime(date_str, "%Y.%m.%d").date()
            elif '年' in date_str:
                date = datetime.strptime(date_str, "%Y年%m月%d日").date()
            else:
                date = datetime.strptime(date_str, "%Y%m%d").date()
    except ValueError:
        pass
    
    return date


def find_platform():
    """
    返回平台信息
    window平台返回：windows
    linux平台返回：linux
    """
    os_platform = platform.system().lower()
    if os_platform == "linux":
        return "linux"
    elif os_platform == "darwin":
        return "mac"
    else:
        return "windows"


def get_season():
    """
    获取当前季度
    """
    now = datetime.now()
    season = 1  # 季度
    last_month = 3  # 当前季度最后一个月份
    if now.month > 9:
        season = 4
        last_month = 12
    elif now.month > 6:
        season = 3
        last_month = 9
    elif now.month > 3:
        season = 2
        last_month = 6

    return now.year, season, last_month


def get_final_date():
    """
    按季度收费（现在基本上都是按季度收费),返回当期季度的最后一天
    """
    year, season, last_month = get_season()
    if last_month == 12:
        year = year + 1 # 下一年
        last_month = 1 # 下一年的一月
    else:
        last_month = last_month + 1
    finaldate = datetime.strptime(str(year)+"/"+str(last_month)+"/01",
                             "%Y/%m/%d").date()
    print(finaldate)
    return finaldate


def diff_month(d1, d2):
    """
    获取两个日期之间有多少个月
    test cases:
    assert diff_month(datetime(2010,10,1), datetime(2010,9,1)) == 1
    assert diff_month(datetime(2010,10,1), datetime(2009,10,1)) == 12
    assert diff_month(datetime(2010,10,1), datetime(2009,11,1)) == 11
    assert diff_month(datetime(2010,10,1), datetime(2009,8,1)) == 14
    """
    return (d1.year - d2.year) * 12 + d1.month - d2.month

 
def getDistanceFromPointToLine(a, b, c, xy): 
    if isinstance(xy["longitude"], str):
        x =float( xy["longitude"])
    else:
        x =  xy["longitude"]
    
    if isinstance(xy["latitude"], str):
        y = float(xy["latitude"])
    else:
        y =  xy["latitude"]
    
    try:
        return abs((a * x + b * y + c) / sqrt(a * a + b * b))
    except ZeroDivisionError:
        print(a, b)
        return 0
    except TypeError:
        print(xy)
        return 0


if __name__ == "__main__":
    print(verify_email("ddd@163.com"))
    print(verify_email("dd 163.com"))
