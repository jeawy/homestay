import requests, sys
import json, pdb
import pdb 


def send_sms(smstype, phone, code = None, **kwargs):
    """
    短信发送模板：只支持注册、密码找回、密码修改三种
    smstype: register(注册)， find_password(密码找回), reset_pwd(重置密码)
    phoen: 手机号码
    code: 验证码
    """
    host = 'https://gyytz.market.alicloudapi.com/sms/smsSend'
    
    appcode = "b8da29c7215347d4b46581b54980b5c5"  
    sms_content = ""
    querys = 'mobile='+phone  
    smsSignId = 'bede794d598349fba839384b584733ec' # 社区互通签名ID
    param = None
    if smstype == '1' or smstype == '0':
        # 您的验证码是:{0}。
        param = "&param=**code**:{0}".format(code)  
        querys +=  "&templateId=4dfa0e1af2f4495c8a6c3b65344b2a5e"  
    elif smstype == "reset_pwd":
        # 您正在找回密码，验证码是：{0}。
        param = "&param=**code**:{0}".format(code)  
        querys +=  "&templateId=bc7daea997084e9bb311183ecab2b12c" 
    elif smstype == 'newbills':# 【{0}】有新订单  
        querys +=  "&templateId=ac1fc82ddb8d490782bf60170faa7117" 
    elif smstype == 'card': # 【{0}】有新的购物卡需要激活   
        querys +=  "&templateId=51994dcba005432ea1016b4b6e912be6"  
    elif smstype == 'cardactivate': # 【{0}】您的购物卡已激活,祝您购物愉快!   
        querys +=  "&templateId=85b80c171d2b4ed59622de9f25b489e8"     
    elif smstype == "fahuo":
        # 发货
        param = "&param=**product**:{0}".format(code)  
        querys +=  "&templateId=5d35d47fe4124618988f63547903334f"
    elif smstype == "getpassword":
        # 获取卡密
        param = "&param=**password**:{0}".format(code)  
        querys +=  "&templateId=60e0cb74420f48aabee95b0f0e52047b"    
    elif smstype == 'sys':# 系统错误提醒
        param = "&param=**reason**:{0}".format(code)  
        querys +=  "&templateId=76c1b2e4666b4ca5b402dbbd7bd297f1"  
    else:
        return 1, "短信类型错误" 

    if param is not None:
        querys += param

    querys += '&smsSignId='+smsSignId 
    url = host  + '?' + querys
    headers = {'Authorization': 'APPCODE ' + appcode}
    requests.post(url,headers=headers )  
    return 0, sms_content
     
 