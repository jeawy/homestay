from area.models import Area
import pdb


def get_parent(area):
    # 递归获取完整的省市区地址：陕西省 西安市 莲湖区
    try:
        parent = area.PARENT_ID 
        try: 
            parent  = Area.objects.get(ID = parent.ID)
            return get_parent(parent) + " " + area.NAME
        except Area.DoesNotExist:
            return parent.NAME + " " + area.NAME
        
    except Area.DoesNotExist:
        return area.NAME
     
        
def get_parent_id(area):
    # 递归获取完整的省市区地址：陕西省 西安市 莲湖区
    try:
        parent = area.PARENT_ID 
        try: 
            parent  = Area.objects.get(ID = parent.ID)
            return get_parent_id(parent) + [area.ID]
        except Area.DoesNotExist:
            return [parent.ID] +  [area.ID]
        
    except Area.DoesNotExist:
        return [area.ID]
     