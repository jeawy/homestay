import pdb
from tags.models import Tags 

def add(name, label):
    # 添加标签，如果标签的名称或者label存在的话，返回false, tagid，否则返回True, tagid
    try:
        tag = Tags.objects.get(name = name)
    except Tags.DoesNotExist:
        try:
            tag = Tags.objects.get(name = name)
        except Tags.DoesNotExist:
            tag = Tags.objects.create(name = name, label = label)
            return True, tag
    return False, tag
