from dept.models import Dept
from property.code import ERROR, SUCCESS 

def check_alias(alias, excludeid = None):
    """
    部门别名校验
    :param alias:
    :return:
    """
    result = {
        'status': SUCCESS
    }
    if len(alias) > 128:
        result['status'] = ERROR
        result['msg'] = '别名太长.'
        return result
    elif len(alias) == 0:
        result['status'] = ERROR
        result['msg'] = '别名不能为空.'
        return result
    elif check_alias_exist(alias, excludeid = excludeid):
        result['status'] = ERROR
        result['msg'] = '别名重复.'
        return result
    return result

def get_user_dict(user):
    user_dict =  {
                    "id":user.id,
                    "name":user.username,
                    "dept_id":user.dept.id,
                    "dept_name":user.dept.name,
    }
    return user_dict

def get_dept_dict(dept ):
    """
    返回deptment的字典实例
    字典格式：
     {
                    "name":dept.name,
                    "level":dept.level,
                    "charger_name":charger_name,
                    "charger_id": charger_id,
                    "top_dept_name":top_dept_name,}
                    "top_dept_id":top_dept_id
                    }
    """
    charger_name = ""
    charger_id = ""
    dept_alias = ""
    
    if dept.charger: 
        charger_name = dept.charger.username
        charger_id = dept.charger.id
    parentid = 0
    if dept.parent:
        parentid = dept.parent.id
    if dept.alias:
        dept_alias = dept.alias
    """
    children_num = Dept.objects.filter( parent__id = dept.id ).count()

    dept_dict = {
                    "id":dept.id,
                    "name":dept.name,
                    "level":dept.level,
                    "charger_name":charger_name,
                    "charger_id": charger_id,
                    "children_num":children_num, 
    } 
    """
    dept_dict = {
                    "id":dept.id,
                    "name":dept.name,
                    "level":dept.level,
                    "charger_name":charger_name,
                    "alias": dept_alias,
                    "charger_id": charger_id,
                    "parentid":parentid,
                    "children":[], 
    } 
    children = Dept.objects.filter( parent__id = dept.id)
    if children:
        for child in children: 
            dept_dict['children'].append(get_dept_dict(child ))
        return dept_dict
    else: 
        return dept_dict

def check_name_exist(name, community, excludeid = None):
    """检查部门名称是否已经存在，如果存在返回True，否则返回False"""
    if excludeid:
        # 排除指定id记录
        return Dept.objects.filter(name = name, community= community).exclude(id = excludeid).exists()
    else:
        return Dept.objects.filter(name = name, community= community).exists()

def check_alias_exist(alias, excludeid = None):
    """检查部门别名是否已经存在，如果存在返回True，否则返回False"""
    if excludeid:
        # 排除指定id记录
        return Dept.objects.filter(alias = alias).exclude(id = excludeid).exists()
    else:
        return Dept.objects.filter(alias = alias).exists()

