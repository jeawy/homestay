# 编码规范
# 1 都大写
# 2 只有成功时，才返回0，其他时候返回非0状态码
# 3 每个错误状态码之后，都要注释状态码表示的意义
# 4 错误状态码前，前缀APP名，可以是缩写


# ###################################################
#
# 公共状态码
# #################################################### 
SUCCESS = 0
NOTFOUND = 404 # 
ERROR = 1 # 错误统计代码
ARGUMENT_ERROR_ID_NOT_INT = 405 # 前端传的id不是整数, id not int
VALUEERROR_INT = 406 # 数据格式错误【需要整数类型】 数据在转int的时候发生value error错误，如 int('zhang')
IMAGE_FILE_TYPE_ERROR = 407 # 图片格式错误，只接受：png jpeg和jpg

# ###################################################
#
# DEPT 类别 相关错误代码
# #################################################### 
DEPTNOTEXIST = 11000 # 未找到部门
DEPT_NOTFOUND = 11404 # '404 Not found the id'
DEPT_ARGUMENT_ERROR_NEED_NAME_ID = 11001 # 'Need name and id  in POST'
DEPT_ARGUMENT_ERROR_NEED_ID = 11002 # 'Need id  in POST'
DEPT_ARGUMENT_ERROR_NEED_NAME = 11003 # 'Need NAME  in POST'
DEPT_PARENTID_NOTFOUND = 11405 # '404 Parent DEPT not found ID:{}'.format(parentid) 
DEPT_ARGUMENT_ERROR_NAME_TOO_LONG = 11004 # 'name too long.'
DEPT_ARGUMENT_ERROR_NAME_EMPTY = 11005 # 'name is empty.'
DEPT_ARGUMENT_ERROR_CHANGR_NOT_FOUND = 11406 # 部门负责人没有找到 
DEPT_DUPLICATED_NAME = 11006 # 部门名称已存在 

# ###################################################
#
# CATEGORY 类别 相关错误代码
# ####################################################
CATEGORY_NOTFOUND = 12404 # '404 Not found the id'
CATEGORY_ARGUMENT_ERROR_NEED_NAME_ID = 12001 # 'Need name and id  in POST'
CATEGORY_ARGUMENT_ERROR_NEED_ID = 12002 # 'Need id  in POST'
CATEGORY_ARGUMENT_ERROR_NEED_NAME = 12003 # 'Need NAME  in POST'
CATEGORY_PARENTID_NOTFOUND = 12405 # '404 Parent Category not found ID:{}'.format(parentid) 

# ###################################################
#
# TASK 类别 相关错误代码
# ####################################################
TASK_NOTFOUND = 13404 # '404 Not found the id'
TASK_ARGUMENT_ERROR_NEED_NAME = 13001 # 'Need name, content, start_date, end_date, total_hour, executorlist, projects_id, type in POST'
TASK_ARGUMENT_ERROR_NAME_TOO_LONG = 13002 # 'name too long.'
TASK_ARGUMENT_ERROR_NAME_EMPTY = 13003 # 'name is empty.'
TASK_ARGUMENT_ERROR_DATETIME_FORMAT = 13004 # 'date time format is error.'
TASK_ARGUMENT_ERROR_DATE_FORMAT = 13005 # 'date format is error.'
TASK_ARGUMENT_ERROR_START_DATE = 13006 # 'Task start_date is error.'
TASK_ARGUMENT_ERROR_END_DATE = 13007 # 'Task end_date is error.'
TASK_ARGUMENT_ERROR_EXECUTOR_NOT_FOUND = 13008 # 'executor not found.'
TASK_ARGUMENT_ERROR_ASSOCIATE_TASK_NOT_FOUND = 13009 # 'associate_task not found.'
TASK_ARGUMENT_ERROR_PARENTID_EMPTY = 13010 # 'parent id is empty.'
TASK_ARGUMENT_ERROR_STATUS_NOT_FOUND = 13011 # 'status not found.'
TASK_ARGUMENT_ERROR_CONTENT_EMPTY = 13012 # 'task content id empty.'
TASK_ARGUMENT_ERROR_MANAGER_IS_EMPTY = 13013 # 'task manager is empty.'
TASK_ARGUMENT_ERROR_PARENTID_IS_NOT_INT = 13014 # 'parent task id is format error in post.'
TASK_ARGUMENT_ERROR_TASKID_IS_EMPTY = 13015 # 'parent task id is empty in task.'
TASK_ARGUMENT_ERROR_PARENTID_IS_EMPTY = 13016 # 'parent id is empty.'
TASK_ARGUMENT_ERROR_NEED_TOTAL_HOUR = 13017 # 'Need total_hour in POST.'
TASK_ARGUMENT_ERROR_NEED_CONTENT = 13018 # 'Need content in POST.'
TASK_ARGUMENT_ERROR_EXTRA_IS_EMPTY = 13019 # 'extra_attr is empty.'
TASK_ARGUMENT_ERROR_NEED_STATUS = 13020 # 'Need status in POST.'
TASK_ARGUMENT_ERROR_PRIORITY_NOT_FOUND = 13021 # 'priority not found.'
TASK_ARGUMENT_ERROR_NEED_START_DATE = 13022 # 'Need start_date in POST.'
TASK_ARGUMENT_ERROR_NEED_END_DATE = 13023 # 'Need end_date in POST.'
TASK_ARGUMENT_ERROR_STATUS_NOT_COMPLETED = 13024 # 'previous task is not completed.'
TASK_STATUS_IS_COMPLETED = 13024 # 'task is completed.'
TASK_STATUS_IS_TIMEOUT = 13025 # 'task status is timeout.'
TASK_ARGUMENT_ERROR_PARENT_TASK_TOTAL_HOUR_IS_SMALL = 13026 # 'Parent total_hour is small than child task.'
TASK_ARGUMENT_ERROR_CAN_NOT_POST_NEW_TASK = 13027 # 'Child task total_hour is bigger than parent task.'
TASK_ARGUMENT_ERROR_TOTAL_HOUR_IS_TOO_LONG = 13028 # 'Task total_hour is too long.'
TASK_ARGUMENT_ERROR_TYPE_EMPTY = 13029 # 'Need type in POST.'
TASK_ARGUMENT_ERROR_NEED_PROJECTS_ID = 13030 # 'Need projects_id in POST.'
TASK_ARGUMENT_ERROR_NEED_ID = 13031 # 'Need id in POST'
TASK_ARGUMENT_ERROR_STATUS = 13032 # 'Task status is error.'
TASK_ARGUMENT_ERROR_TOTAL_HOUR = 13033 # 'Task total_hour is error.'
TASK_ARGUMENT_ERROR_PRIORTY = 13034 # 'Task priority is error.'
TASK_ARGUMENT_ERROR_TYPE = 13035 # 'Task type is error.'
TASK_ARGUMENT_ERROR_PROJECTS = 13036 # 'Task projects is error.'
TASK_ARGUMENT_ERROR_EXECUTOR = 13037 # 'Task executors_list is error.'
TASK_ARGUMENT_ERROR_ATTACHMENT = 13038 # 'Task attachment is error.'
TASK_ARGUMENT_ERROR_MANAGER = 13039 # 'Task manager is error.'

TASKEXECUTOR_ARGUMENT_ERROR_NEED_EXECUTOR = 13039 # 'Need executorlist in POST.'

ASSOCIATETASK_ARGUMENT_ERROR_TYPE_NOT_FOUND = 13040 # 'type not found.'

TASKEXECUTORRECORD_ARGUMENT_ERROR_ID_NOT_INT = 13041 # 'labor_hour not int.'
TASKEXECUTORRECORD_ARGUMENT_ERROR_NEED_LABOR_HOUR = 13042 # 'Need labor_hour in POST.'
TASKEXECUTORRECORD_ARGUMENT_ERROR_SCHEDULE = 13043 # 'schedule is error.'
TASKEXECUTORRECORD_ARGUMENT_ERROR_CONTENT_EMPTY = 13044 # 'completed content is empty.'
TASKEXECUTORRECORD_ARGUMENT_ERROR_NEED_CONTENT = 13045 # 'Need content in POST.'
TASKEXECUTORRECORD_ARGUMENT_ERROR_NEED_TASKID = 13046 # 'Need task_id in POST.'
TASKEXECUTORRECORD_ARGUMENT_ERROR_SMALL_OR_BIG = 13047 # 'labor_hour is small or big.'
TASKEXECUTORRECORD_ARGUMENT_ERROR_TASK_EXECUTOR = 13048 # 'Task executor is not match.'
TASKEXECUTORRECORD_ARGUMENT_ERROR_NEED_TITLE = 13049 # 'Need title in POST.'
TASKEXECUTORRECORD_ARGUMENT_ERROR_NEED_TASK_TYPE = 13050 # 'Need task type in POST.'
TASKEXECUTORRECORD_NOTFOUND = 13051 # '404 Not found the TaskExecutorRecord id'
TASK_ARGUMENT_ERROR_TOTAL_HOUR_EMPTY = 13052 # 'task total_hour is empty.'
TASK_EXECUTOR_RECORD_NOTFOUND = 13053 # '404 Not found the TaskExecutorRecord id'
TASK_ARGUMENT_ERROR_CHILD_TASK_STATUS_NOT_COMPLETED = 13054 # 'Child task is not completed.'
TASK_ARGUMENT_ERROR_ASSOCIATE_TASK = 13055 # 'Task associated_list is error.'


# ###################################################
#
# USER 用户管理 相关错误代码
# ####################################################
USER_NOT_REGISTERED = 14001 # 用户未注册
USER_ROLEID_EMPTY = 14002 # 角色id列表不能为空
USER_ROLE_ID_VALUE_ERROR = 14003 # role id不能是非数字型的字符串，如："dd32d"为非法字符
USER_ARGUMENT_ERROR_NEED_USERID_ROLEIDS = 14004 # 'Need userid and roleids in POST'
USER_NOT_FOUND = 14005 # 未找到指定用户


# ####################################################
#
# WKTEMPLATE 流程模板 相关错误代码
# ####################################################

WKTEMPLATE_ARGUMENT_ERROR_NAME_EMPTY = 15001 #模板名称为空'name is empty'
WKTEMPLATE_ARGUMENT_ERROR_TYPE_EMPTY = 15002 #模板分类为空 'Need type in POST'
WKTEMPLATE_ARGUMENT_ERROR_TYPE_NOT_FOUND = 15002 #模板分类没有找到 '404 Not find the type'
WKTEMPLATE_ARGUMENT_ERROR_DEPT_NOT_FOUND = 15003 # 部门没有找到
WKTEMPLATE_ARGUMENT_ERROR_STATUS_EMPTY = 15004 #模板类型为空 'status is empty'
WKTEMPLATE_ARGUMENT_ERROR_STATUS_NOT_FOUND = 15005 # 模板类型没有找到 '404 Not find the status'
WKTEMPLATE_ARGUMENT_ERROR_APPROVE_RULE_EMPTY = 15006#审批人员为空 'approve_rule is empt'
WKTEMPLATE_ARGUMENT_ERROR_NAME_TOO_LONG = 15007 # 模板名称太长'name too long.'
WKTEMPLATE_DUPLICATED_NAME = 15008  #模板名称已存在
WKTEMPLATE_ARGUMENT_ID_NOTFOUND = 15009 #'Not find the id'
WKTEMPLATE_ARGUMENT_ID_EMPTY = 15010 #'id is empty'
WKTEMPLATE_ARGUMENT_ERROR_NEED_ID = 15011 # 'Need id in POST'
WKTEMPLATE_ARGUMENT_STATUS_IS_DRAFT = 15012 # 'template status is draf'
WKTEMPLATE_ARGUMENT_DEPT_IS_NOT_INT = 15013 # 'dept is not int'
WKTEMPLATE_ARGUMENT_ERROR_DEPT_EMPTY = 15014 # 'Need dept in POST'
WKTEMPLATE_ARGUMENT_ERROR_DEPT_DUPLICATE = 150015 #'404 dept is duplicate'
# ###################################################
#
# WKRECORDS 流程 相关错误代码
# ####################################################
WKRECORDS_RECORD_ARGUMENT_ERROT_CATEGORY_ID_NOT_LEGAL = 16001 #流程列别不在数据库中
WKRECORDS_RECORD_ARGUMENT_ERROR_CATEGORY_ID_NOT_INT = 16002 #流程类别不是整数
WKRECORDS_RECORD_ARGUMENT_ERROR_NAME_TOO_LONG =16003 #流程名太长
WKRECORDS_RECORD_ARGUMENT_ERROR_NAME_IS_EMPTY = 16004 #流程名为空
WKRECORDS_RECORD_ARGUMENT_ERROR_NEED_NAME = 16005 #流程名不存在
WKRECORDS_RECORD_ARGUMENT_ERROR_NEED_CONTEXT = 16006 #当提交的时候，缺少详细内容
WKRECORDS_RECORD_ARGUMENT_ERROR_STATUS_ERROR =16007 #提交的状态错误
WKRECORDS_RECORD_ARGUMENT_ERROR_NEED_STATUS = 16008 #缺少状态
WKRECORDS_RECORD_ARGUMENT_ERROR_CONTEXT_IS_EMPTY = 16009 #提交的内容为空
WKRECORDS_RECORD_ARGUMENT_ERROR_TEMPLATE_NOT_EXIST = 16010 #提交的模板错误，不在模板表中
WKRECORDS_RECORD_ARGUMENT_ERROR_TEMPLATE_IS_NOT_INT = 16011 #提交的模板不是整数
WKRECORDS_RECORD_ARGUMENT_ERROR_STATUS_NOT_INT = 16012 #状态不是整数
WKRECORDS_EXTRA_ARGUMENT_ERROR = 16013 #扩展属性值错误
WKRECORDS_APPROVER_ARGUMENT_ERROR_EXTRA_VALUE_NOT_DICT = 16014 #扩展属性的值不是dict
WKRECORDS_APPROVER_ARGUMENT_ERROR_APPROVER_IS_EMPTY = 16015 #审批人员为空
WKRECORDS_APPROVER_ARGUMENT_ERROR_APPROVER_LIST_VALUE_ERROR = 16016 #传进后台的审批人员列表值错误
WKRECORDS_APPROVER_ARGUMENT_ERROR_APPROVER_NOT_DICT = 16017 #审批人员不是dict
WKRECORDS_APPROVER_ARGUMENT_ERROR_LEVEL_IS_NOT_INT = 16018 #审批级别不是整数
WKRECORDS_APPROVER_ARGUMENT_ERROR_ORDER_IS_NOT_LEGAL = 16019 #审批次序不是从1或1
WKRECORDS_APPROVER_ARGUMENT_ERROR_APPROVER_VALUE_NOT_LIST = 16020 #审批人员ID的存储不是列表
WKRECORDS_APPROVER_ARGUMENT_ERROR_APPROVER_NOT_EXIST = 16021 #审批人员不存在
WKRECORDS_APPROVER_ARGUMENT_ERROR_NEED_APPROVER = 16022 #没有提交审批人员
WKRECORDS_APPROVER_ARGUMENT_ERROR_APPROVER_CAN_NOT_SELF = 16023 #审批人员不可以是自己
WKRECORDS_RECEIVER_ARGUMENT_ERROR_RECEIVER_LIST_VALUE_ERROR = 16024 #收文人员值错误
WKRECORDS_RECEIVER_ARGUMENT_ERROR_RECEIVER_NOT_EXIST = 16025 #收文人员不在用户表中
WKRECORDS_RECEIVER_ARGUMENT_ERROR_RECEIVER_AND_APPROVER_IS_SAME = 16026 #收人人员和审批人员相同
WKRECORDS_RECEIVER_ARGUMENT_ERROR_RECEIVER_CAN_NOT_SELF = 16027 #收文人员不可以是自己
WKRECORDS_ASSOCIATE_ARGUMENT_ERROR_ASSOCIATE_ERROR = 16028 #关联表不是list
WKRECORDS_ASSOCIATE_ARGUMENT_ERROR_ASSOCIATE_NOT_EXIST = 16029 #关联流程不存在
WKRECORDS_RECEORD_SAVE_ERROR = 16030 #保存记录失败
WKRECORDS_RECORD_NOT_FOUND = 16404 #没有发现有关ID的记录
WKRECORDS_ID_IS_EMPTY = 16031 #提供的ID为空
WKRECORDS_RECORD_ARGUMENT_ERROR_NEED_ID = 16032 #删除记录没有提供记录ID
WKRECORDS_RECORD_ARGUMENT_ERROR_ID_NOT_INT = 16033 #记录ID不是int
WKRECORDS_NOT_FOUND = 16033 #没有发现流程
WKRECORDS_CAN_NOT_CHANGE = 16034 #流程已审核或者审核中，不可以修改流程
WKRECORDS_NOT_RIGHTS_CHANGE = 16035 #不可以修改他人的流程
WKRECORDS_ARGUMENT_ERROR_NEED_ID = 16036 #没有提供流程ID
WKRECORDS_RECEIVER_ARGUMENT_ERROR_RECEIVER_REPEAT = 16037 #收文人员重复
WKRECORDS_APPROVER_ARGUMENT_ERROR_APPROVER_REPEAT = 16038 #审批人员重复
WKRECORDS_ASSOCIATE_ARGUMENT_ERROR_ASSOCIATE_REPEAT = 16039 #关联流程重复
WKRECORDS_RECALL_FAIL = 16040 #撤回失败
WKRECORDS_CAN_NOT_RECALL = 16041 #流程已经审批，不可以进行撤回
WKRECORDS_APPROVER_NOT_FOUND = 16042 #找不到审批人员
WKRECORDS_APPROVER_CAN_NOT_APPROVE = 16043 #当前审批人员不可以进行审批
WKRECORDS_APPROVER_STATUS_NOT_INT = 16044 #审批状态不是int
WKRECORDS_APPROVER_STATUS_NOT_LEGAL = 16045 #审批状态不合法
WKRECORDS_APPROVER_STATUS_NOT_FOUND = 16046 #没有提供审批状态
WKRECORDS_APPROVER_OPINION_IS_EMPTY = 16047 #审批意见为空
WKRECORDS_APPROVER_OPINION_NOT_FOUND = 16048 #没有提供审批意见
WKRECORDS_APPROVER_TOUSER_ERROR = 16049 #提供的转批人员错误
WKRECORDS_APPROVER_TOUSER_NOT_FOUND = 16050 #没有提供转批人员
WKRECORDS_EXTRA_ARGUMENT_ERROR_EXTRA_LIST_NAME_ERROR = 16051 #扩展属性内容有不带引号的字符错误
WKRECORDS_APPROVER_ARGUMENT_ERROR_APPROVER_LIST_TYPE_ERROR = 16052 #审批人员类型错误
WKRECORDS_APPROVER_ARGUMENT_ERROR_APPROVER_LIST_SYNTAX_ERROR = 16053 #审批列表语法错误
WKRECORDS_RECEIVER_ARGUMENT_ERROR_RECEIVER_LIST_TYPE_ERROR = 16054 #收文人员列表类型错误
WKRECORDS_RECEIVER_ARGUMENT_ERROR_RECEIVER_LIST_SYNTAX_ERROR = 16055 #收文列表语法错误
WKRECORDS_RECEIVER_ARGUMENT_ERROR_RECEIVER_NOT_LIST = 16056 #收文列表不是list
WKRECORDS_EXTRA_ARGUMENT_ERROR_EXTRA_LIST_TYPE_ERROR = 16057 #扩展属性列表类型错误
WKRECORDS_EXTRA_ARGUMENT_ERROR_EXTRA_LIST_SYNTAX_ERROR = 16058 #扩展属性语法错误
WKRECORDS_ASSOCIATE_ARGUMENT_ERROR_ASSOCIATE_LIST_NAME_ERROR = 16059 #关联列表里有未加引号的字符
WKRECORDS_ASSOCIATE_ARGUMENT_ERROR_ASSOCIATE_LIST_TYPE_ERROR = 16060 #关联列表类型错误
WKRECORDS_ASSOCIATE_ARGUMENT_ERROR_ASSOCIATE_LIST_SYNTAX_ERROR = 16061 #关联列表语法错误
WKRECORDS_RECORD_ARGUMENT_ERROT_CATEGORY_ID_NOT_EXIST =  16062 #类别不存在
WKRECORDS_RECORD_ARGUMENT_ERROT_NEED_CATETORY_IN_POST = 16063 #需要类别在post里面
WKRECORDS_ASSOCIATE_ARGUMENT_ERROR_VALUE_NOT_INT = 16064 #关联列表里面的值不是int
WKRECORDS_APPROVER_ARGUMENT_ERROR_APPROVER_NOT_INT = 16065 #审批人员的值不是int
WKRECORDS_RECEIVER_ARGUMENT_ERROR_RECEIVER_NOT_INT = 16066 #收文人员的值不是int

# ###################################################
#
# APPFILE  相关错误代码
# ####################################################
APPFILE_TYPE_ERROR = 17001 # 文件类型不在系统识别范围内



######################################################
#
#RULE 规则相关错误代码
######################################################
RULE_ARGUMENT_ERROR_NAME_TOO_LONG = 18001 # 'name too long.'
RULE_ARGUMENT_ERROR_NAME_NOTFOUND = 18002 # 'Need rule_name in POST '
RULE_ARGUMENT_ERROR_NAME_EMPTY = 18003 # 'name is empty.'
RULE_ARGUMENT_ERROR_APPROVE_TYPE_EMPTY = 18004 # 'approve_type is empty.'
RULE_ARGUMENT_ERROR_APPROVE_LEVEL_EMPTY = 18005 # '没有审批环节.'
RULE_NOTFOUND = 18006 #'404 This id not mapping a rule'
RULE_ARGUMENT_ERROR_USER_ID_EMPTY = 18007 # 'user_id is empty.'
RULE_ARGUMENT_ERROR_ID_EMPTY = 18008  #'id is empty.'
RULE_ARGUMENT_ERROR_DEPT_NOT_ROLE = 18009 #'该部门没有该角色'
RULE_ARGUMENT_ERROR_USER_ID_NOT_FOUND = 18010 #'user_id not find'


######################################################
#
#ATTRS 属性管理 相关错误代码
######################################################
class ATTRS(object):
    """
    属性管理状态码
    """
    ATTRS_NOTFOUND = 19404 # '404 Not found the id'
    ATTRS_ARGUMENT_ERROR_NEED_NAME = 19001 # 'Need NAME in POST'
    ATTRS_ARGUMENT_ERROR_NAME_TOO_LONG = 19002 # 'name too long.'
    ATTRS_ARGUMENT_ERROR_NAME_DUPLICATED = 19003 # 'name duplicated.'
    ATTRS_ARGUMENT_ERROR_VALUE_NOT_NUMBER = 19004 # 'value not number'
    ATTRS_ARGUMENT_ERROR_DATE_FORMAT = 19005 # 'date format is error.'
    ATTRS_ARGUMENT_ERROR_BOOL_FORMAT = 19006 # 'boolean format is error.'
    ATTRS_ARGUMENT_ERROR_SELECTWAY = 19007 # 'selectway is error.'
    ATTRS_ARGUMENT_ERROR_VALUE_IS_NULL = 19008 # 'value is null.'
    ATTRS_ARGUMENT_ERROR_KEY_LESS_TWO = 19009 # 'key is less than two'
    ATTRS_ARGUMENT_ERROR_VALUE_DUPLICATED = 19010 # 'duplicate value'
    ATTRS_ARGUMENT_ERROR_SELECTKEY_NOT_EXIST = 19011 # 'select key is not exist'
    ATTRS_ARGUMENT_ERROR_TYPE_NOT_ENUMERATE = 19012 # 'type not enumerate'
    ATTRS_NOTFOUND_TYPE = 19013 # '404 Not find the type'
    ATTRS_ARGUMENT_ERROR_NEED_TYPR = 19014 # 'Need type in POST'
    ATTRS_ARGUMENT_ERROR_NEED_ID = 19015 # 'Need id in POST'
    ATTRS_ARGUMENT_ERROR_ENTITY_TYPE_NOT_FOUND = 19016 # 'entity_type not found'
    ATTRS_ARGUMENT_ERROR_ENTITY_TYPE_NOT_INT = 19017 # 'entity_type not int'
    ATTRS_ARGUMENT_ERROR_NAME_NOT_EXIST = 19018 # 'name is not exist'
    ATTRS_ARGUMENT_ERROR_ATTR_TYPE_NOT_FIND = 19019 # 'attr_type not find'
    ATTRS_ARGUMENT_ERROR_ATTR_TYPE_NOT_INT = 19020 # 'attr_type not int'
    ATTRS_ARGUMENT_ERROR_NEED_ATTR_TYPE = 19021 # 'Need attr_type in POST'
    ATTRS_ARGUMENT_ERROR_ENTITY_NOT_FOUND = 19022 # 'entity_id or entity_type not found'
    ATTRS_ARGUMENT_ERROR_ENTITY_NOT_INT = 19023 # 'entity_id or entity_type not int'
    ATTRS_ARGUMENT_ERROR_NEED_ATTR_ID = 19024 # 'Need attr id in POST'
    ATTRS_ARGUMENT_ERROR_NEED_ENTITY_TYPR = 19025 # 'Need entity type in POST'
    ATTRS_ARGUMENT_ERROR_NEED_ENTITY_ID = 19026 # 'Need entity id in POST'
    ATTRS_ARGUMENT_ERROR_NEED_ATTR_VALUE = 19027 # 'Need attr_value in POST'
    ATTRS_ARGUMENT_ERROR_NEED_ATTR_NAME = 19028 # 'Need attr_name in POST'
    ATTRS_ARGUMENT_ERROR_NOT_DICT = 19029 # '填写属性实体时，传递的属性列表不是个字典列表'
    ATTRS_ARGUMENT_ERROR_DICT_MISS_FIELD_OR_FILE_ERROR = 19030 # '字典属性字段缺失或填写错误'
    ATTRS_NOTFOUND_ATTR_TYPE = 19031 # '404 Not find the attr type'
    ATTRS_ARGUMENT_ERROR_NAME_EMPTY = 19032 # 'name is empty.'
    ATTRS_ARGUMENT_ERROR_VALUE_TOO_LONG = 19033 # 'value too long.'
    ATTRS_ARGUMENT_ERROR_VALUE_EMPTY = 19034 # 'value is empty.'


######################################################
#
#PROJECTS项目管理相关错误代码
######################################################
class PROJECT(object):
    """
    项目管理状态码
    """
    PROJECT_NAME_TOO_LONG = 20001 # 项目名称太长.
    PROJECT_ARGUMENT_ERROR_NAME_EMPTY = 20002 # 项目名称不能为空.
    PROJECT_DUPLICATED_NAME = 20003 # 项目名称重复
    PROJECT_ARGUMENT_ERROR_CHANGR_NOT_FOUND = 20004 # 没有找到部门负责人信息
    # Need name, code, start and end in POST 
    PROJECT_ARGUMENT_ERROR_NEED_NAME = 20005  

    PROJECT_DUPLICATED_CODE = 20006 # 项目名称重复
    PROJECT_CODE_TOO_LONG = 20007 # 编码太长.
    PROJECT_ARGUMENT_ERROR_NEED_CODE = 20008 # 请填写编码

    PROJECT_ARGUMENT_ERROR_START = 20009 # 项目起始日期格式错误
    # 项目起始日期小于今天
    PROJECT_ARGUMENT_ERROR_START_EARLY_THAN_TODAY = 20010 
    # 结束日期不能小于起始日期
    PROJECT_ARGUMENT_ERROR_END_EARLY_THAN_START = 20011  
    # 项目结束日期格式错误
    PROJECT_ARGUMENT_ERROR_END = 20012  
    # 预算数字格式错误
    PROJECT_BUDGET_ERROR = 20014
    # 状态status不是int型数据
    PROJECT_ARGUMENT_ERROR_STATUS = 20015 
    # 创建项目时，状态只能是草稿：0，正在进行：1
    PROJECT_ARGUMENT_ERROR_STATUS_DRAFT_ACTIVE = 20016


    # 未找到指定项目
    PROJECT_NOT_FOUND = 20017  
    # 参数错误：需要传递项目id，id
    PROJECT_ARGUMENT_NEED_ID = 20018

    
######################################################
#
#OPRECORDS 操作记录管理 相关错误代码
######################################################
class OPRECORDS(object):
    """
    操作记录管理状态码
    """
    OPRECORDS_RECORDS_NOTFOUND = 21404  # '404 Not found the id'
    OPRECORDS_ARGUMENT_ERROR_ENTITY_TYPE_NOT_FOUND = 21001 # 'entity_type not found'
    OPRECORDS_ARGUMENT_ERROR_ENTITY_TYPE_NOT_INT = 21002 # 'entity_type not int'
    OPRECORDS_ARGUMENT_ERROR_ENTITY_ID_NOT_INT = 21003 # 'entity id not int'
    OPRECORDS_ARGUMENT_ERROR_URL_TOO_LONG = 21004 # 'url too long.'
    OPRECORDS_ARGUMENT_ERROR_URL_EMPTY = 21005 # 'url is empty.'
    OPRECORDS_ERROR_ID_NOT_INT = 21006 # 'id not int'



######################################################
#
#COMMENT 评论/备注管理 相关错误代码
######################################################
class COMMENT(object):
    """
    评论/备注管理状态码
    """
    COMMENT_ARGUMENT_ERROR_CONTENT_EMPTY = 22001 # 'content is empty.'
    COMMENT_ARGUMENT_ERROR_ENTITY_TYPE_NOT_FOUND = 22002 # 'entity_type not found'
    COMMENT_ARGUMENT_ERROR_ENTITY_TYPE_NOT_INT = 22003 # 'entity_type not int'
    COMMENT_ARGUMENT_ERROR_PID_NOT_INT = 22004 # 'pid not int.'
    COMMENT_ARGUMENT_ERROR_PID_NOT_FOUND = 22005 # 'pid not found.'
    COMMENT_ARGUMENT_ERROR_NEED_CONTENT = 22006 # 'Need content in POST.'
    COMMENT_ARGUMENT_ERROR_NEED_PID = 22007 # 'Need pid in POST.'
    COMMENT_ARGUMENT_ERROR_NEED_ENTITY_ID = 22008 # 'Need entity id in POST.'
    COMMENT_ARGUMENT_ERROR_NEED_ENTITY_TYPE = 22009 # 'Need entity type in POST.'
    COMMENT_ARGUMENT_ERROR_NEED_ID = 22010 # 'Need id in POST'
    COMMENT_ID_NOTFOUND = 22011 # '404 Not found the id'
    COMMENT_ARGUMENT_ERROR_VALUE_NOT_INT = 22012 # 'value not int'



######################################################
#
#ASSETS资产管理相关错误代码
######################################################
class ASSETS(object):
    """
    项目管理状态码
    """
    ASSETS_NAME_TOO_LONG = 23001 # '资产名称太长.'
    ASSETS_ARGUMENT_ERROR_NAME_EMPTY = 23002 # '资产名称不能为空.'
    # Need name, code, start and end in POST 
    ASSETS_ARGUMENT_ERROR_NEED_NAME = 23003
    # 未找到指定资产
    ASSETS_NOT_FOUND = 23004
    ASSETS_ARGUMENT_NEED_ID_OR_IDS = 23005  # 'Need id or ids in POST'
    ASSETS_ARGUMENT_ERROR_NEED_NAME_AND_PATH = 23006  # 'Need name and path in POST'
    ASSETS_PATH_TOO_LONG = 23007 # '路径太长.'
    ASSETS_ARGUMENT_ERROR_PATH_EMPTY = 23008 # '路径不能为空.'
    ASSETS_CATEGORY_NOTFOUND = 23009 # 'Not find the category'
    ASSETS_ARGUMENT_CATEGORY_NOT_INT = 23010 # 'category not int'
    ASSETS_TEAM_NOTFOUND = 23011 # 'Not find the team'
    ASSETS_ARGUMENT_TEAM_NOT_INT = 23012 # 'team not int'
    ASSETS_INNER_VERSION_TOO_LONG = 23013 # '内部资产版本号太长.'
    ASSETS_OUTER_VERSION_TOO_LONG = 23014 # '外部资产版本号太长.'
    ASSETS_ARGUMENT_ERROR_PRIORTY = 23015 # 'assets priority is error.'
    ASSETS_ARGUMENT_ERROR_PRIORITY_NOT_FOUND = 23016 # 'priority not found.'
    ASSETS_ARGUMENT_ERROR_NEED_PRIORITY = 23017 # 'Need priority id in POST'
    ASSETS_ARGUMENT_ERROR_NEED_LEVEL = 23018 # 'Need level id in POST'
    ASSETS_ARGUMENT_ERROR_LEVEL = 230019 # 'assets level is error.'
    ASSETS_ARGUMENT_ERROR_LEVEL_NOT_FOUND = 230020 # 'level not found.'
    ASSETS_PROJECT_NOTFOUND = 230021 # 'Not find the project'
    ASSETS_ARGUMENT_PROJECT_NOT_INT = 230022 # 'project not int'
    ASSETS_TASK_NOTFOUND = 230023 # 'Not find the task'
    ASSETS_ARGUMENT_TASK_NOT_INT = 23024 # 'task not int'
    ASSETS_ARGUMENT_ERROR_NAME_DUPLICATED = 23025 # '资产名称重复'



    PROJECT_DUPLICATED_CODE = 20006 # 项目名称重复
    PROJECT_CODE_TOO_LONG = 20007 # 编码太长.
    PROJECT_ARGUMENT_ERROR_NEED_CODE = 20008 # 请填写编码

    PROJECT_ARGUMENT_ERROR_START = 20009 # 项目起始日期格式错误
    # 项目起始日期小于今天
    PROJECT_ARGUMENT_ERROR_START_EARLY_THAN_TODAY = 20010 
    # 结束日期不能小于起始日期
    PROJECT_ARGUMENT_ERROR_END_EARLY_THAN_START = 20011  
    # 项目结束日期格式错误
    PROJECT_ARGUMENT_ERROR_END = 20012 
    
    # 预算数字格式错误
    PROJECT_BUDGET_ERROR = 20014
    # 状态status不是int型数据
    PROJECT_ARGUMENT_ERROR_STATUS = 20015 
    # 创建项目时，状态只能是草稿：0，正在进行：1
    PROJECT_ARGUMENT_ERROR_STATUS_DRAFT_ACTIVE = 20016


    # 未找到指定项目
    PROJECT_NOT_FOUND = 20017  
    # 参数错误：需要传递项目id，id
    PROJECT_ARGUMENT_NEED_ID = 20018



######################################################
#
#DIR 文件目录 相关错误代码
######################################################
class DIR(object):
    DIR_ARGUMENT_ERROR_NEED_TITLE = 24001 # 'Need title id in POST'
    DIR_ARGUMENT_ERROR_NAME_TOO_LONG = 24002 # 'title too long'
    DIR_ARGUMENT_ERROR_NAME_EMPTY = 24003 # 'title is empty.'
    DIR_ARGUMENT_ERROR_PARENT_NOT_INT = 24004 # 'parent not int'
    DIR_NOTFOUND = 24005 # '404 Not found the id'



######################################################
#
#LINKS 制作环节 相关错误代码
######################################################
class LINKS(object):
    LINKS_ARGUMENT_ERROR_NEED_LINKS = 25001 # 'Need links in POST'
    LINKS_ARGUMENT_ERROR_CONTENT_EMPTY= 25002 #'Content is empty'
    LINKS_ARGUMENT_ERROR_START_EARLY_THAN_TODAY = 25003 # 'start date cannot be less than today'
    LINKS_ARGUMENT_ERROR_START = 25004  #'start date format error'
    LINKS_ARGUMENT_ERROR_END_EARLY_THAN_START = 25005 # 'The end date cannot be less than the start date'
    LINKS_ARGUMENT_ERROR_END = 25006 #'End date format error'
    ASSETS_ARGUMENT_ID_NOT_INT = 25007 #'assets id not int'
    DEPT_ARGUMENT_ERROR_ID_NOT_FOUND = 25008 #'dept is not found'
    DEPT_ARGUMENT_ID_NOT_INT = 25009 # 'dept is not int'
    LINKS_ARGUMENT_ERROR_NOT_EXIST= 25010 #'links is not exist'

######################################################
#
# 系统配置
######################### 
OUTSOURCING = 'outsourcing' # 外包部门
CLIENT = 'client' # 客户部门
SYSSECTION = 'syssection'
# 外审系统配置
CLIENTSERVER = 'clientserver' 
SERVERHOST = 'host'
SERVERPORT = 'port'

# 实训成员的上下班、工时计算配置
TRAINING_WORKTIME = 'training_worktime'
TRAINING_WORKTIME_ON = 'training_worktime_on' # 上班时间
TRAINING_WORKTIME_OFF = 'training_worktime_off' # 下班时间
TRAINING_WORKTIME_LONG = 'training_worktime_long' # 工作时长

# 正式成员的上下班、工时计算配置
OFFICIAL_WORKTIME = 'official_worktime'
OFFICIAL_WORKTIME_ON = 'official_worktime_on' # 上班时间
OFFICIAL_WORKTIME_OFF = 'official_worktime_off' # 下班时间
OFFICIAL_WORKTIME_LONG = 'official_worktime_long' # 工作时长

# 实训排名计算权重
TRAINING_RANGE = 'training_range'
 
ATTENDANCE = 'attendance'  # 考勤
SCORE = 'score' # 评分
RANGE = 'range' # 排名
SUBMIT_TIME = 'submit_time' # 提交时间


####   支付方式
ZHIFUBAO = 0
WEIXIN = 1
YUE = 2 # 余额支付