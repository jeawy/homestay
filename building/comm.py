#! -*- coding:utf-8 -*-
import json
import operator
import pdb 
import time
from datetime import datetime
from functools import reduce
import uuid
from django.utils.translation import ugettext as _ 
from common.utils import format_all_dates, verify_phone
from dept.models import Dept
from appuser.models import AdaptorUser as User 
from excel.excel import readExcel
from excel.imageparsing import compenent 
from property.code import ERROR, SUCCESS
from property import settings
from property.entity import EntityType
from common.logutils import getLogger
from django.conf import settings  
from building.models import RoomDynamicFeeDetail
logger = getLogger(True, 'building', False)
 
from building.models import Building, Unit, Room

def get_room_feestatus_txt(status):
    """
    获取缴费状态的文字说明
    """
    status = int (status)
    if (status == 1) :
        return "正常"
    else:
        return "已欠费"



def get_units(units):
    """
    获取单元号字典
    """
    unit_ls = []
    for unit in units:
        unit_dict = {}
        unit_dict["building"] = unit.building.name
        unit_dict["buildinguuid"] = unit.building.uuid
        unit_dict["uuid"] = unit.uuid
        unit_dict["name"] = unit.name
        unit_ls.append(unit_dict)

    return unit_ls

def get_single_building_dict(building):
    """
    """
    building_dict = {}
    building_dict['uuid'] = building.uuid
    building_dict['name'] = building.name 
    building_dict['community_uuid'] = building.community.uuid
    building_dict['community_name'] = building.community.name
    building_dict['level'] = 1 # 楼号
    building_dict['children'] = [] # 单元号
    
    for unit in building.building_unit.all().order_by("name"):
        unit_dict = {}
        unit_dict['uuid'] = unit.uuid
        unit_dict['name'] = unit.name
        unit_dict['level'] = 2 # 单元号
        building_dict['children'].append(unit_dict)
 
    return building_dict

def get_single_room_dict(room, fee = False):
    # fee = True时表示请求需要带上物业信息
    room_dict = {}
    room_dict['uuid'] = room.uuid
    room_dict['name'] = room.name
    room_dict['area'] = room.area
    room_dict['status'] = room.status 
    room_dict['unit_name'] =  room.unit.name
    room_dict['building_name'] =  room.unit.building.name
    room_dict['communityname'] =  room.community.name
    room_dict['communityuuid'] =  room.community.uuid
    dynamic_fees = list(RoomDynamicFeeDetail.objects.filter(room = room).\
        values( "dynamicfee__name" )) 
    room_dict['dynamic_fees'] = dynamic_fees
    
    #room_dict['users'] = [(roomer.phone,  roomer.username) for roomer in room.roomers.all()]
    room_dict['owner'] = {
        "username":"",
         "phone":"",
    }
    if room.owner:
        room_dict['owner'] = {
            "username":room.owner.username,
            "phone":room.owner.phone,
        }
    if fee: 
        if room.fixed_fee: # 物业费收费方式已设置
            room_dict['fixed_fee'] = {
                "name": room.fixed_fee.name,
                "uuid":room.fixed_fee.uuid
            }
        else:
            room_dict['fixed_fee'] = None
        
        if room.arrearage_start_date:
            room_dict['arrearage_start_date'] = time.mktime(room.arrearage_start_date.timetuple())
        else:
            room_dict['arrearage_start_date'] = None
        room_dict['arrearage'] = room.arrearage
        room_dict['fee_status'] = room.fee_status 
      
         
        
    return room_dict


def get_room_detail(room):
    """
    获取房屋的全部详细信息：
    房号、单元号、楼号、房屋面积
    业主信息：姓名、手机号码、uuid
    物业费收取方式、其他非统一收费内容
    缴费状态：正常、欠缴费、欠缴费起始日期
    """
    room_dict = {}
    room_dict['uuid'] = room.uuid
    room_dict['name'] = room.name
    room_dict['area'] = room.area
    room_dict['unitname'] = room.unit.name
    room_dict['building'] = room.unit.building.name
    room_dict['status'] = room.status
    room_dict['buildinguuids'] =  [ room.unit.building.uuid, room.unit.uuid] 
 
    if room.fixed_fee: # 物业费收费方式已设置
        room_dict['fixed_fee'] = {
            "name": room.fixed_fee.name,
            "uuid":room.fixed_fee.uuid
        }
    else:
        room_dict['fixed_fee'] = None
    
    if room.arrearage_start_date:
        room_dict['arrearage_start_date'] = time.mktime(room.arrearage_start_date.timetuple())
    else:
        room_dict['arrearage_start_date'] = None
    room_dict['arrearage'] = room.arrearage
    room_dict['fee_status'] = room.fee_status
      
    dynamic_fees = list(RoomDynamicFeeDetail.objects.filter(room = room).\
        values("dynamicfee__uuid", "dynamicfee__name", "start_date"))
    for dynamic_fee in dynamic_fees:
        dynamic_fee['start_date'] = dynamic_fee['start_date'].strftime(settings.DATEFORMAT)
    room_dict['username'] = ""
    room_dict['phone'] = ""
    room_dict['dynamic_fees'] = dynamic_fees
     
    if room.owner:
        room_dict['username'] = room.owner.username
        room_dict['phone'] = room.owner.phone


    return room_dict

def get_msgrecord_dict(records):
    """
    催缴记录详情
    """
    records_ls = []
    for record in records:
        record_dict = {}
        record_dict['username'] = record.user.username
        record_dict['reminder_date'] = time.mktime( record.reminder_date.timetuple())
        record_dict['reminder_type'] = record.reminder_type
        record_dict['detail'] = record.detail
        records_ls.append(record_dict)
    return records_ls


def create_asset(asset_json, community, user):
    """
    前端传json，批量新建资产
     {"keys": ["building_name", "unit_name", "roomname", "area"],
                      "values":
                          [["22栋", "1单元", "1023", "100",],
                          ["22栋", "1单元", "1023", "100",],
                          ["22栋", "1单元", "1023", "100",],
                          ["22栋", "1单元", "1023", "100",] ],
                      "community_uuid":""}
    返回result
    """
    # 失败数量
    failure_num = 0 
    # 成功数量
    success_num = 0
    # 因为重复跳过的数量
    duplicate_num = 0
    result = {
        "status": SUCCESS,
        "msg": "",
        "json": "",
        "user": ""
    }
    content = []
    asset_values = asset_json["values"]
    asset_keys = asset_json["keys"]
    for values in asset_values:
        i = 0 
        try:
            building_name_index = asset_keys.index('building_name')
            building_name = values[building_name_index] 
        
            building, created = Building.objects.get_or_create(name = building_name, 
            community = community)
            if created:
                building.uuid = uuid.uuid4()
                building.save()
             
            unit_name_index = asset_keys.index('unit_name')
            unit_name = values[unit_name_index] 
            unit, created = Unit.objects.get_or_create(name = unit_name, building=building)
            if created:
                unit.uuid = uuid.uuid4()
                unit.save()
            roomname_index = asset_keys.index('roomname')
            roomname = values[roomname_index] 
            room, created = Room.objects.get_or_create(name = roomname, unit=unit)
            if created:
                room.uuid = uuid.uuid4()
                room.save()
            try:
                area_index = asset_keys.index('area')
                area = values[area_index]
                room.area = area
                room.save()
            except ValueError:
                pass 

            try:
                arrearage_start_date_index = asset_keys.index('arrearage_start_date')
                arrearage_start_date = values[arrearage_start_date_index]
                if arrearage_start_date:
                    if len(arrearage_start_date) > 8:
                        arrearage_start_date = arrearage_start_date.strip().split(" ")
                        if len(arrearage_start_date) > 0:
                            arrearage_start_date = format_all_dates(arrearage_start_date[0])
                            if arrearage_start_date is not None:
                                room.arrearage_start_date = arrearage_start_date 
                                room.save()
            except ValueError:
                pass 

            # 业主信息
            try:
                phone_index = asset_keys.index('phone')
                phone = str(values[phone_index])
                if verify_phone(phone):
                    try:
                        user = User.objects.get(phone = phone)
                    except User.DoesNotExist:
                        # 创建业主信息
                        user = User.objects.create(uuid= uuid.uuid4(),phone=phone
                        )
                    room.owner = user
                    room.save()
            except ValueError:
                pass 

            try:
                # 更新业主名字
                username_index = asset_keys.index('username')
                username = values[username_index]
                if  username is not None and len(username) > 0: 
                    room.owner.username = username
                    room.owner.save()
            except ValueError:
                pass
            success_num += 1

        except ValueError:
            failure_num += 1 
            
         
    result["failure_num"] = failure_num
    result["success_num"] = success_num
    result["json"] = content
    logger.debug("batch add building data:{0}".format(str(asset_json)))
    logger.info("success_num:{0},failure_num:{1}".format(success_num,failure_num))
    return result
 

def get_asset_json(assets):
    """
    返回简单的资产列表数据：仅仅包括：id和资产名称
    """
    asset_list = []
    for asset in assets:
        asset_dict = {}
        asset_dict['id'] = asset.id
        asset_dict['name'] = asset.name
        asset_dict['asset_type'] = asset.asset_type
        asset_list.append(asset_dict)
    return asset_list


def varify_data(data):
    if 'name' in data:
        name = data['name'].strip()
        if len(name) > 28:
            return 1, "房号名字过长，最大28"
    
    if 'area' in data:
        area = data['area'].strip()
        try:
            float(area)
        except ValueError:
            return 1, "房屋面积不是数字"
    
    return 0, ""