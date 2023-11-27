import pdb
from tags.models import Tags 

def add(name, label):
    # 添加标签，如果标签的名称或者label存在的话，返回false, tagid，否则返回True, tagid 
    tag, created= Tags.objects.get_or_create(name = name, label = label)
    return  tag
            
