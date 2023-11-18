# 个推相关接口
import hashlib
import time
from turtle import pd
from django.conf import settings
import requests
import pdb
import json 


def get_token():
    # 获得个推的token
    t = time.time()
    stamptime = int(round(t * 1000))
    appkey = settings.UNIAPP['AppKey']
    appid = settings.UNIAPP['APPID']
    master_secret = settings.UNIAPP['MasterSecret']
    apiurl = settings.GETUI['baseapi'] + "/auth" 

    sign = hashlib.sha256((appkey+str(stamptime)+master_secret).encode("utf-8")).hexdigest()
    
    data = {
        "sign":sign,
        "timestamp":stamptime,
        "appkey":appkey 
    }

    req = requests.post(url=apiurl, data = json.dumps(data),
           headers={'Content-Type':'application/json;charset=utf-8'} )
     
    if req.status_code == 200:
        return json.loads(req.content)['data']['token']
    else:
        return None

def send_single_notice():
    # 个推推送消息，API参考https://docs.getui.com/getui/server/rest_v2/push/
    # 这只是一个demo
    token = get_token()
    
    if token is None:
        # 打日志，获取token失败
        pass
    else:
        data = {
            "request_id":"12258123473236279",
            "settings":{
                "ttl":3600000,
                "strategy":{  
                    "default":1  
                }
            },
            "audience":{
                "cid":[
                    "8f686629fc5dad0e9ab47b47f3b2a859"
                ]
            },
            "push_message":{
                "notification":{
                    "title":"停电通知",
                    "body":"即将停电，请保活",
                    "click_type":"url",
                    "url":"https//:proprety.chidict.com"
                } 
            },
            "push_channel":{ 
            "ios":{  
                    "type":"notify",  
                    "payload":"自定23义消息",  
                    "aps":{  
                        "alert":{  
                            "title":"苹果离线展示的标题",  
                            "body":"苹果离线展示的内容"  ,
                            "subtitle":"ddddddddd"
                        },  
                        "content-available":0  
                    },  
                    "sound":"ddd",
                    "auto_badge":"+1"  
                }  
            }
        }
        apiurl = settings.GETUI['baseapi'] + "/push/single/cid"
        req = requests.post(url=apiurl, data = json.dumps(data),
            headers={'Content-Type':'application/json;charset=utf-8', "token":token} )
         
        if req.status_code == 200:
            return json.loads(req.content)['data'] 
        else:
            return None
