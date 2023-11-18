 
from django.conf import settings
import requests
import json


def get_access_token():
    # 获取微信小程序的access token
    # API:https://developers.weixin.qq.com/miniprogram/dev/api-backend/open-api/access-token/auth.getAccessToken.html
    secret = settings.WEIXINPAY['xiaochengxu']['app_seckey']
    app_id = settings.WEIXINPAY['xiaochengxu']['app_id']
    url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={0}&secret={1}'.format(app_id, secret)
    res = requests.get(url)
    if res.status_code == 200:
        # 获取成功
        result = json.loads(res.text)
        if 'access_token' in result:
            access_token = result['access_token'] # token  
            expires_in = result['expires_in'] # token 过期时间 单位：秒

            print(expires_in)
        else:
            # 获取失败，给管理者发短信
            pass
    else:
        # 获取失败，给管理者发短信
        pass