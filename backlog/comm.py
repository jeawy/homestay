

from backlog.models import Backlog

def get_unfinished_count(user):
    #  返回某个用户的未完成的待办总数
    return Backlog.objects.filter(user = user, status = Backlog.WAIT).count()
