 
from common.logutils import getLogger
import pdb
import json 
from django.http import HttpResponse
from django.views import View
from property.code import ERROR, SUCCESS
from community.comm_statistics import  community_statatics
 
from community.models import Community 

logger = getLogger(True, 'community_stat', False)
    
class CommunityStatView(View):  
    """
    短信及账户金额变更的时候，应该调用这个接口进行
    """
    def post(self, request):
        """
        更新接口
        """
        result = {
            'status': SUCCESS,
            "msg":""
        } 
        communities = Community.objects.all()  
        for community in  communities:
            community_statatics(community) 
        logger.debug("小区总金额、总收入、短信余额、今日收入已更新")
        return HttpResponse(json.dumps(result), content_type="application/json")
  