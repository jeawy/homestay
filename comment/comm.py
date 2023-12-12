import time
import pdb
from comment.models import Comment, CommentImgs
from property.code import ERROR, SUCCESS
from property.entity import EntityType
from django.db.models import Sum, Avg
from product.models import Product


def cal_rate(entity_uuid, entity_type):

    if int(entity_type) == EntityType.PRODUCT:
        # 只有商品才需要评分 
        kwargs = {}
        kwargs['entity_uuid'] = entity_uuid 
        kwargs['entity_type'] = entity_type 
        kwargs['pid__isnull'] = True 
        rates = Comment.objects.filter( **kwargs).aggregate(
                        Avg("rate"), Avg("real_rate"), Avg("service_rate"), 
                        Avg("health_rate"), Avg("location_rate"), 
                    )
        
        total_rate = 0 
        if rates['service_rate__avg']:
            total_rate += round (rates['service_rate__avg'], 1) 
        
        if rates['health_rate__avg']:
            total_rate += round (rates['health_rate__avg'], 1) 
        
        if rates['real_rate__avg']:
            total_rate += round (rates['real_rate__avg'], 1) 
        
        if rates['location_rate__avg']:
            total_rate += round (rates['location_rate__avg'], 1) 

        total_rate = total_rate / 4 

        try:
            product = Product.objects.get(uuid =entity_uuid )
            product.rate = round(total_rate, 1)
            product.save()
        except Product.DoesNotExist:
            pass
 
def get_comments_list(comments):
    '''
        返回comment的列表,递归方式
        格式：[
        {
            "id": comment.id,
            "entity_uuid": comment.entity_uuid,
            "entity_type": comment.entity_type,
            "content": comment.content,
            "pid": comment.pid,
            "attachment":attachment_list
        }]
        '''
    comment_list = []
    for comment in comments:
        # 附件列表  
        img_list = list(CommentImgs.objects.filter(comment = comment)\
            .values_list("filepath"))
         
        sub_comment_list = [] 
        # 获取子评论
        sub_comments = Comment.objects.filter( pid = comment)
        if sub_comments:
            sub_comment_list = get_comments_list(sub_comments)
        # 评论者信息
        user_dict={
            'thumbnail_portait':comment.user.thumbnail_portait,
            'username':comment.user.username,
            'uuid':comment.user.uuid
        }
        if comment.pid:
            parent = comment.pid.user.username
        else:
            parent = None
        comment_dict = { 
            "uuid": comment.uuid,
            "images":img_list, 
            "content": comment.content,
            "date": time.mktime(comment.date.timetuple()),
            "subs": sub_comment_list, # 子评论 
            "user": user_dict,
            "rate": comment.rate,

            "real_rate": comment.real_rate,
            "service_rate": comment.service_rate,
            "health_rate": comment.health_rate,
            "location_rate": comment.location_rate,

            
            "comeway": comment.comeway,
            "parent":parent
        }
        comment_list.append( comment_dict )

    return comment_list

def get_2_comments_list(comments):
    comment_list = []
    for comment in comments:
        # 附件列表  
        img_list = list(CommentImgs.objects.filter(comment = comment)\
            .values_list("filepath"))
         
        sub_comment_list = [] 
        # 获取子评论
        sub_comments = Comment.objects.filter( pid = comment)
        if sub_comments:
            sub_comment_list += get_2_comments_list(sub_comments)
        # 评论者信息
        user_dict={
            'thumbnail_portait':comment.user.thumbnail_portait,
            'username':comment.user.username,
            'uuid':comment.user.uuid
        }
        if comment.pid:
            parent = comment.pid.user.username
        else:
            parent = None
        comment_dict = { 
            "uuid": comment.uuid,
            "images":img_list, 
            "content": comment.content,
            "date": time.mktime(comment.date.timetuple()), 
            "user": user_dict,
            "rate": comment.rate,

            "real_rate": comment.real_rate,
            "service_rate": comment.service_rate,
            "health_rate": comment.health_rate,
            "location_rate": comment.location_rate,


            "comeway": comment.comeway,
            "parent":parent
        }
        comment_list.append( comment_dict )

    return comment_list + sub_comment_list


def get_comments_sub_list(comments):
    '''
        返回comment的列表,非递归方式
        格式：[
        {
            "id": comment.id,
            "entity_uuid": comment.entity_uuid,
            "entity_type": comment.entity_type,
            "content": comment.content,
            "pid": comment.pid,
            subs:[],//非递归方式
            "attachment":attachment_list
        }]
        '''
    comment_list = []
    for comment in comments:
        # 附件列表  
        img_list = list(CommentImgs.objects.filter(comment = comment)\
            .values_list("filepath"))
         
        sub_comment_list = [] 
        # 获取子评论
        sub_comments = Comment.objects.filter( pid = comment)
        if sub_comments:
            sub_comment_list = get_2_comments_list(sub_comments)
        # 评论者信息
        user_dict={
            'thumbnail_portait':comment.user.thumbnail_portait,
            'username':comment.user.username,
            'uuid':comment.user.uuid
        }
        if comment.pid:
            parent = comment.pid.user.username
        else:
            parent = None
        comment_dict = { 
            "uuid": comment.uuid,
            "images":img_list, 
            "content": comment.content,
            "date": time.mktime(comment.date.timetuple()),
            "subs": sub_comment_list, # 子评论 
            "user": user_dict,
            "rate": comment.rate, 

            "real_rate": comment.real_rate,
            "service_rate": comment.service_rate,
            "health_rate": comment.health_rate,
            "location_rate": comment.location_rate,


            "comeway": comment.comeway,
            "parent":parent
        }
        comment_list.append( comment_dict )

    return comment_list


# PID验证
def check_pid(pid, comment, result):
    if pid:
        try:
            pid = int(pid)
            try:

                parent_id = Comment.objects.get(id=pid)
                comment.pid = parent_id
                return True
            except Comment.DoesNotExist:
                result['status'] =ERROR
                result['msg'] = 'pid not found.'
                return False
        except ValueError:
            result['status'] = ERROR
            result['msg'] = 'pid not int.'
            return False
    else:
        # pid默认为None
        comment.pid_id = None
        return True
  