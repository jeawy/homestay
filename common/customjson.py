from django.core.serializers.json import DjangoJSONEncoder
from datetime import datetime
from django.conf import settings
import pdb
import time

class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            #return obj.strftime(settings.DATETIMEFORMAT)
            # 返回时间戳
            return time.mktime(obj.timetuple())
        return super().default(obj)

 