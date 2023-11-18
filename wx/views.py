from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
import json
import hashlib
import pdb
from django.conf import settings
import requests
from wx.comm import get_access_token 

class WxMsgView(View):

    def get(self, request):
        # 微信消息
        content= {} 
        if 'signature' in request.GET and 'timestamp' in request.GET and \
            'nonce' in request.GET and 'echostr' in request.GET:
            signature = request.GET['signature']
            timestamp = request.GET['timestamp']
            nonce = request.GET['nonce']
            echostr = request.GET['echostr']
            token = settings.WEIXINPAY['msg']['token'] 
            strsss = [token, timestamp, nonce]
            # 对token、timestamp和nonce按字典排序 
            strsss.sort() 
            strsss = "".join(strsss) 
            mysignature = hashlib.sha1(strsss.encode('utf8')).hexdigest()
           
            if mysignature == signature:
                # 验证通过 https://developers.weixin.qq.com/miniprogram/dev/framework/server-ability/message-push.html
                return HttpResponse(echostr)
            else:
                pass
        else:
            # 不是来自微信
            get_access_token()
            
        return HttpResponse(json.dumps(content),content_type="application/json")

    def post(self, request):
        content = {} 
        """
        https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/subscribe-message.html#%E8%AE%A2%E9%98%85%E6%B6%88%E6%81%AF%E8%AF%AD%E9%9F%B3%E6%8F%90%E9%86%92
        微信发过来的request.body中的消息为
        {
            "ToUserName": "gh_123456789abc",
            "FromUserName": "o7esq5OI1Uej6Xixw1lA2H7XDVbc",
            "CreateTime": "1620973045",
            "MsgType": "event",
            "Event": "subscribe_msg_popup_event",
            "List": [   {
                    "TemplateId": "hD-ixGOhYmUfjOnI8MCzQMPshzGVeux_2vzyvQu7O68",
                    "SubscribeStatusString": "accept",
                    "PopupScene": "0"
                }],
            }
        参数	说明
        ToUserName	小程序帐号ID
        FromUserName 用户openid
        CreateTime	时间戳
        TemplateId	模板id（一次订阅可能有多个id）
        SubscribeStatusString订阅结果（accept接收；reject拒收）
        PopupScene	弹框场景，0代表在小程序页面内
        """
        print( request.body  ) 
        data =    {
        "touser": "o5z6I4vAAeRsPeamGQm12k-1zMrY",
        "template_id": "II8z6lrkimKxNKNmvjtPnLr3_SkBEquRxfBi0Tzc9UE",
        "page": "/pages/index/index",
        "miniprogram_state":"developer",
        "lang":"zh_CN",
        "data": {
            "thing1": {
                "value": "停电通知"
            },
            "thing2": {
                "value": "2015年01月05日"
            },
            "thing3": {
                "value": "TIT创意园"
            } ,
            "thing4": {
                "value": "广州市新港中路397号"
            } ,
            "time5": {
                "value": "2022年02月26日 20:49"
            }
          }
        }
        access_token = '54_TU5yFhyhqw9aJz1kN7Jea9OLyhUMGlLYUGCqI1t166O4xc9-KNk6aJOlQaqSWoYxQapeXLavLbHQx2YQWd51cXEmQ1FcYLCuc_98cQn8Guw7A1oXjgnOW2gWCoYrjeVU5FSV2-GvUv0C4yOVKIFdAJACAX'
        url = "https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token=" + access_token
        res = requests.post(url=url, data = json.dumps(data))
   
        print(res)
        return HttpResponse(json.dumps(content),content_type="application/json")
