# -*- coding:utf-8 -*-
#Author： 

import pdb
import socket
import string
import time
import random
import requests
import string
import json
import hashlib
import xmltodict 
import re 
from django.conf import settings
from common.logutils import getLogger
logger = getLogger(True, 'pay', False)

class PayToolUtil(object): 
    _SUCCESS = 'SUCCESS'
    def __init__(self,sub_mch_id="", app=False, way="sub"):
        # way = sub表示子商户方式支付
        # sub_mch_id 微信支付分配的子商户号,仅在服务商模式下使用
        # app 表示在APP中的支付
        # ========支付相关配置信息===========
        self.way = way
        self.sub_mch_id = settings.WEIXINPAY_SUB_MCH['sub_mch_id']
        self.app = app
        if way == "sub":
            if app:
                self._APP_ID = settings.WEIXINPAY_SUB_MCH['app']['app_id']  # 公众账号appid
            else:
                self._APP_ID = settings.WEIXINPAY_SUB_MCH['xiaochengxu']['app_id']  # 公众账号appid
            self._MCH_ID = settings.WEIXINPAY_SUB_MCH['mch_id']  # 商户号
            # key设置路径：微信商户平台(pay.weixin.qq.com) -->账户设置 -->API安全 -->密钥设置
            self._API_KEY = settings.WEIXINPAY_SUB_MCH['apikey']  
        else:
            self._APP_ID = settings.WEIXINPAY['web']['app_id']  # 公众账号appid
            self._MCH_ID = settings.WEIXINPAY['mch_id']  # 商户号
            # key设置路径：微信商户平台(pay.weixin.qq.com) -->账户设置 -->API安全 -->密钥设置
            self._API_KEY = settings.WEIXINPAY['apikey']  

        # 有关url
        self._host_name = socket.gethostname()
        self._ip_address = socket.gethostbyname(self._host_name)
        self._CREATE_IP = self._ip_address  # 发起支付的ip
        
        self._UFDODER_URL = "https://api.mch.weixin.qq.com/pay/unifiedorder"
        self._QUERY_URL = "https://api.mch.weixin.qq.com/pay/orderquery"
        self._NOTIFY_URL = settings.DOMAINHOST + "api/pay/weixin/"#"your Ip：端口／处理方法路径"  # 微信支付结果回调的处理方法
        
        

    def getPayUrl(self,orderid, goodsName, goodsPrice, openid=None,   **kwargs):
        '''
        向微信支付端发出请求，web获取url, 微信小程序获取config字典，服务商模式下的APP支付
        APP支付接口：https://pay.weixin.qq.com/wiki/doc/api/app/app_sl.php?chapter=9_1
        ''' 
        appid = self._APP_ID
        mch_id = self._MCH_ID
        key = self._API_KEY
        nonce_str = str(int(round(time.time() * 1000)))+str(random.randint(1,999))+" ".join(random.sample(['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z'], 5)).replace(" ","") #生成随机字符串
        spbill_create_ip = self._CREATE_IP
        notify_url = self._NOTIFY_URL
         
        params = {}
        params['appid'] = appid
        params['mch_id'] = mch_id

        if self.way == "sub":
            # 支付到子服务商
            params['sub_mch_id'] = self.sub_mch_id
            if openid is not None:
                params['openid'] = openid
                trade_type = "JSAPI" # 小程序支付
            else:
                trade_type = "APP" # APP 支付
        else:
            trade_type = "NATIVE" # 扫码支付
 
        params['nonce_str'] = nonce_str
        params['out_trade_no'] = orderid#.encode('utf-8')    #客户端生成并传过来，参数必须用utf8编码，否则报错
        params['total_fee'] = goodsPrice   #单位是分，必须是整数
        params['spbill_create_ip'] = spbill_create_ip
        params['notify_url'] = notify_url 
        params['body'] = goodsName  
        params['trade_type'] = trade_type 
       
        #生成签名
        ret = []
        for k in sorted(params.keys()):
            if (k != 'sign') and (k != '') and (params[k] is not None):
                ret.append('%s=%s' % (k, params[k]))
        params_str = '&'.join(ret)
        params_str = '%(params_str)s&key=%(partner_key)s'%{'params_str': params_str, 'partner_key': key}
     
        params_str = hashlib.md5(params_str.encode('utf-8')).hexdigest() 
        sign = params_str.upper()
        params['sign'] = sign 
        #拼接参数的xml字符串
        request_xml_str = '<xml>'
        for key, value in params.items():
            if isinstance(value, str): 
                request_xml_str = '%s<%s><![CDATA[%s]]></%s>' % (request_xml_str, key, value, key, )
            else:   
                request_xml_str = '%s<%s>%s</%s>' % (request_xml_str, key, value, key, )
        request_xml_str = '%s</xml>' % request_xml_str
        
        #向微信支付发出请求，并提取回传数据 
        res_data = requests.post(self._UFDODER_URL, data=request_xml_str.encode('utf-8')  )  
        res_read = res_data.content
        doc = xmltodict.parse(res_read) 
        return_code = doc['xml']['return_code']
        if return_code=="SUCCESS":
            if self.way == "sub":
                print(doc['xml'])
                # 支付到子商户中
                if self.app: # APP 支付
                    # 调起支付接口
                    # API地址：https://pay.weixin.qq.com/wiki/doc/api/app/app_sl.php?chapter=9_12&index=2
                    prepay_id = doc['xml']['prepay_id']
                    nonce_str = doc['xml']['nonce_str']
                    package = "Sign=WXPay"
                    timestamp = str(int(time.time()))
                    
                    config = {
                        "appid": appid, 
                        "partnerid":self.sub_mch_id,
                        "prepayid":prepay_id,
                        "package": package,
                        "noncestr": nonce_str,
                        "timestamp":timestamp,  
                    }
                     
                    ret = [] 
                    for k in sorted(config.keys()):
                        if (k != 'sign') and (k != '') and (config[k] is not None):
                            ret.append('%s=%s' % (k, config[k]))
                    params_str = '&'.join(ret)
                    params_str = '%(params_str)s&key=%(partner_key)s'%{'params_str': params_str, 'partner_key': self._API_KEY} 
                    params_str = hashlib.md5(params_str.encode('utf-8')).hexdigest() 
                    sign = params_str.upper()
                    config['sign'] = sign 
                    
                else:
                    prepay_id = doc['xml']['prepay_id']
                    nonce_str = doc['xml']['nonce_str']
                    package = "prepay_id="+prepay_id
                    timestamp = str(int(time.time()))
                    
                    config = {
                        "appId": appid, 
                        "timeStamp":timestamp,
                        "nonceStr": nonce_str,
                        "package": package,
                        "signType": "MD5", 
                    }
                    ret = [] 
                    for k in sorted(config.keys()):
                        if (k != 'sign') and (k != '') and (config[k] is not None):
                            ret.append('%s=%s' % (k, config[k]))
                    params_str = '&'.join(ret)
                    params_str = '%(params_str)s&key=%(partner_key)s'%{'params_str': params_str, 'partner_key': self._API_KEY} 
                    params_str = hashlib.md5(params_str.encode('utf-8')).hexdigest() 
                    sign = params_str.upper()
                    config['paySign'] = sign 
                return config
            else:
                # 支付到平台账户中
                result_code = doc['xml']['result_code']
                if result_code=="SUCCESS":
                    code_url = doc['xml']['code_url']
                    return code_url
                else:
                    err_des = doc['xml']['err_code_des']
                    print ("errdes==========="+err_des)
        else:
            fail_des = doc['xml']['return_msg']
            print ("fail des============="+fail_des)
    
    def getQueryUrl(self,orderid, sub_mch_id=None):
        '''
        向微信支付查询接口，获取url
        1232137218973298173
        参考：
        https://pay.weixin.qq.com/wiki/doc/api/native.php?chapter=9_2
        '''
        
        appid = self._APP_ID
        mch_id = self._MCH_ID
        key = self._API_KEY
        nonce_str = str(int(round(time.time() * 1000)))+str(random.randint(1,999))+" ".join(random.sample(['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z'], 5)).replace(" ","") #生成随机字符串
  
        params = {}
        params['appid'] = appid
        params['mch_id'] = mch_id
        params['nonce_str'] = nonce_str
        #客户端生成并传过来，参数必须用utf8编码，否则报错
        params['out_trade_no'] = orderid   
        if sub_mch_id is not None:
            params['sub_mch_id'] = sub_mch_id   
        elif self.sub_mch_id:
            params['sub_mch_id'] = self.sub_mch_id
          
        #生成签名
        ret = []
        for k in sorted(params.keys()):
            if (k != 'sign') and (k != '') and (params[k] is not None):
                ret.append('%s=%s' % (k, params[k]))
        params_str = '&'.join(ret)
        params_str = '%(params_str)s&key=%(partner_key)s'%{'params_str': params_str, 'partner_key': key}
        
        params_str = hashlib.md5(params_str.encode('utf-8')).hexdigest()
        sign = params_str.upper()
        params['sign'] = sign
 
        #拼接参数的xml字符串
        request_xml_str = '<xml>'
        for key, value in params.items():
            if isinstance(value, str):
                request_xml_str = '%s<%s><![CDATA[%s]]></%s>' % (request_xml_str, key, value, key, )
            else:
                request_xml_str = '%s<%s>%s</%s>' % (request_xml_str, key, value, key, )
        request_xml_str = '%s</xml>' % request_xml_str

        #向微信支付发出查询请求，并提取回传数据 
        res_data = requests.post(self._QUERY_URL, data=request_xml_str)
     
        res_read = res_data.content
        doc = xmltodict.parse(res_read)
        print(doc)
        return doc
        
        
        return_code = doc['xml']['return_code']
        if return_code=="SUCCESS":
            result_code = doc['xml']['result_code']
            if result_code=="SUCCESS":
                code_url = doc['xml']['code_url']
                return code_url
            else:
                err_des = doc['xml']['err_code_des']
                print ("errdes==========="+err_des)
        else:
            fail_des = doc['xml']['return_msg']
            print ("fail des============="+fail_des)















