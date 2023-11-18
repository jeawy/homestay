

# 历史操作记录接口
import uuid 
from building.models import RoomFeeOpHistory


def add_history(user, room, detail):
    # 添加操作记录到RoomFeeOpHistory表中
    recorduuid = uuid.uuid4()
    RoomFeeOpHistory.objects.create(uuid=recorduuid, user = user, room = room, detail = detail )