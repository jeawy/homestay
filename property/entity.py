#! -*- coding:utf-8 -*-


class EntityType(object):
    """
    实体类别
    """
    # 任务实体
    TASK = 1
    # 模板实体
    WK_TEMPLATE = 2
    # 登记薄
    RECORD = 3 
    # 项目实体
    PROJECT = 4
    # 资产类别
    ASSET = 5
    # 工种
    WORKTYPE = 6
    # 用户
    USER = 7
    # 实训项目实体
    TRAINING = 8 
    
    # 通知、公告、百事通、社区见闻
    PRODUCT = 9
    # 点赞
    LIKE = 10
    # 维修申请
    REPAIR = 11
    
    # 互助服务
    AID = 12

    # 评论
    COMMENT = 13 

    # 有偿服务
    PAIDSERVICE = 14

    # 账单
    FEE = 15

    # 购物卡
    CARD = 16 

    # 订单
    BILL = 17
    @classmethod
    def get_entities(cls):
        return [cls.TASK, cls.WK_TEMPLATE, cls.RECORD, 
        cls.PROJECT, cls.ASSET, cls.TRAINING , 
        cls.USER,cls.TRAINING, cls.USER,cls.PRODUCT]

class AttrsTypes(object):
    """
    属性类型
    """
    # 数字
    NUMBER = 1
    # 字符
    CHARACTER = 2
    # 日期
    DATE = 3
    # 布尔
    BOOLEAN = 4
    # 枚举
    ENUMERATE = 5
    
    @classmethod
    def get_attrs(cls):
        return [cls.NUMBER, cls.CHARACTER, cls.DATE, cls.BOOLEAN, cls.ENUMERATE]

