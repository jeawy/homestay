import json
import random
import string
import pdb
import time
import os
import socket
import hashlib
from django.conf import settings
import requests
from base64 import b64encode
from Crypto.Signature import pkcs1_15
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256, MD5
from property.code import SUCCESS, ERROR
from common.logutils import getLogger
logger = getLogger(True, 'weixin', False)
import xmltodict 
TIMEOUT = 30


class WeixinPayUtil(object):
    @staticmethod
    def signature(private_key_path, sign_str, md5=False):
        """
        生成签名值
        private_key_path 私钥路径
        sign_str 签名字符串
        md5表示是否用md5进行加密
        https://pay.weixin.qq.com/wiki/doc/apiv3/wechatpay/wechatpay4_0.shtml
        """
        with open(private_key_path) as file:
            private_key = file.read()

        rsa_key = RSA.import_key(private_key)
        signer = pkcs1_15.new(rsa_key)  
        digest = SHA256.new(sign_str.encode('utf-8'))
        return b64encode(signer.sign(digest)).decode('utf-8')

   
class WeixinPay(object):
    """
    微信支付
    """
    base_url = 'https://api.mch.weixin.qq.com'
    # 付款码支付，api：https://pay.weixin.qq.com/wiki/doc/api/micropay_sl.php?chapter=9_10&index=1
    native_url = base_url + "/pay/micropay"
 
    def __init__(self,  sub_mch_id=None, md5=False):
        # md5是否使用MD5加密，uniapp暂时只支持md5加密
        self.key = None
        if sub_mch_id is None:
            # 直接到平台
            mch_id = settings.WEIXINPAY['mch_id']
            app_id = settings.WEIXINPAY['app']['app_id']
            api_v3_key = settings.WEIXINPAY['api_v3_key'] 
            mch_cert_no = settings.WEIXINPAY['serial_no'] 
            notify_url = settings.WEIXINPAY['notifyurl']
            cert_dir = settings.WEIXINPAY['cert_dir']
        else:
            app_id = settings.WEIXINPAY_SUB_MCH['web']['app_id']  # 公众账号appid
            mch_id = settings.WEIXINPAY_SUB_MCH['mch_id']  # 商户号
            # key设置路径：微信商户平台(pay.weixin.qq.com) -->账户设置 -->API安全 -->密钥设置
            self.key = settings.WEIXINPAY_SUB_MCH['apikey']  
            api_v3_key = settings.WEIXINPAY_SUB_MCH['api_v3_key'] 
            mch_cert_no = settings.WEIXINPAY_SUB_MCH['serial_no'] 
            notify_url = settings.WEIXINPAY_SUB_MCH['notifyurl']
            cert_dir = settings.WEIXINPAY_SUB_MCH['cert_dir']

        self.sub_mch_id = sub_mch_id 
        self.mch_id = mch_id
        self.app_id = app_id

        if sub_mch_id is not None:
            self.sub_mch_id = sub_mch_id
        else:
            self.sub_mch_id = None

        self.api_v3_key = api_v3_key
        self.mch_cert_no = mch_cert_no
        self.cert_dir = cert_dir
        self.notify_url = notify_url
        self.md5 = md5

        self.timestamp = str(int(time.time()))
        self.nonce_str = ''.join(random.sample(
            string.ascii_letters + string.digits, 16))

    def _generate_request_sign(self, url_path, data, method='POST'):
        """
        生成请求签名
        """

        sign_list = [method, url_path, self.timestamp, self.nonce_str]
        if data is not None:
            sign_list.append(json.dumps(data))
        else:
            sign_list.append('')
        sign_str = '\n'.join(sign_list) + '\n'
        
        return WeixinPayUtil.signature(private_key_path=os.path.join(self.cert_dir,  "apiclient_key.pem"),
                                       sign_str=sign_str)

    def _generate_pay_sign(self, app_id, package):
        """
        生成支付签名
        """
        sign_list = [app_id, self.timestamp, self.nonce_str, package]
        sign_str = '\n'.join(sign_list) + '\n'
        if self.md5:
            return WeixinPayUtil.signature(private_key_path=os.path.join(self.cert_dir, "apiclient_key.pem"), 
            sign_str=sign_str, md5=True)
        else:
            return WeixinPayUtil.signature(private_key_path=os.path.join(self.cert_dir, "apiclient_key.pem"), sign_str=sign_str)

    def _generate_auth_header(self, signature):
        """
        生成授权请求头
        """
        return f'WECHATPAY2-SHA256-RSA2048  mchid="{self.mch_id}",nonce_str="{self.nonce_str}",' \
               f'signature="{signature}",timestamp="{self.timestamp}",serial_no="{self.mch_cert_no}"'
    
    
    def native_order(self, order_id,  amount, desc, auth_code, mch_id=None, notify_url=None, profit_sharing=False,
                      expire_time=None, attach=None, goods_tag=None, detail=None, scene_info=None, currency='CNY'):
        # 付款码支付(扫码设备进行扫码支付)
        # 主要是业主在PC端支付物业费等费用
        # auth_code: 扫码设备扫描的二维码 
        # API:https://pay.weixin.qq.com/wiki/doc/api/micropay_sl.php?chapter=9_10&index=1
        _host_name = socket.gethostname()
        # 发起支付的ip
        _ip_address = socket.gethostbyname(_host_name)
      
        params = {
            'appid': self.app_id,
            'mch_id': mch_id if mch_id is not None else self.mch_id,
            'sub_mch_id':self.sub_mch_id,
            'nonce_str':self.nonce_str, 
            'body':desc, 
            'out_trade_no': order_id ,
            'total_fee':int(amount * 100),
            'spbill_create_ip':_ip_address,
            'auth_code':auth_code
        }

        #生成签名
        ret = []
        for k in sorted(params.keys()):
            if (k != 'sign') and (k != '') and (params[k] is not None):
                ret.append('%s=%s' % (k, params[k]))
        params_str = '&'.join(ret)
        key = settings.WEIXINPAY_SUB_MCH['apikey'] 
        params_str = '%(params_str)s&key=%(partner_key)s'%{'params_str': params_str, 'partner_key': key}
     
        params_str = hashlib.md5(params_str.encode('utf-8')).hexdigest() 
        sign = params_str.upper()
        params['sign'] = sign 
        logger.error("支付参数:"+str(params))
        #拼接参数的xml字符串
        request_xml_str = '<xml>'
        for key, value in params.items():
            if isinstance(value, str): 
                request_xml_str = '%s<%s><![CDATA[%s]]></%s>' % (request_xml_str, key, value, key, )
            else:   
                request_xml_str = '%s<%s>%s</%s>' % (request_xml_str, key, value, key, )
        request_xml_str = '%s</xml>' % request_xml_str
        
        #向微信支付发出请求，并提取回传数据 
        res_data = requests.post(self.native_url, data=request_xml_str.encode('utf-8')  )  
        res_read = res_data.content
        doc = xmltodict.parse(res_read)  
        return_code = doc['xml']['return_code']
        logger.debug("扫码支付结果:"+str(return_code))
        if return_code=="SUCCESS":
            if doc['xml']['result_code'] == "SUCCESS":
                if doc['xml']['trade_type'] == "MICROPAY":
                    # 交易成功判断条件：return_code和result_code都为SUCCESS且trade_type为MICROPAY
                    # 微信支付订单号
                    transaction_id = doc['xml']['transaction_id']
                    return SUCCESS, transaction_id
                else:
                    logger.error("异常支付:"+str(doc['xml']))
                    return ERROR, "trade_type类型错误"
            else:
                err_code = doc['xml']['err_code']
                if "AUTHCODEEXPIRE" == err_code:
                    # 二维码已过期，请用户在微信上刷新后再试
                    return ERROR, "二维码已过期，请用户在微信上刷新后再试"
                elif "NOTENOUGH" == err_code:
                    # 余额不足
                    return ERROR, "余额不足"
                else:
                    logger.error("支付错误代码:"+str(err_code))
                    return ERROR, "其他错误"
        else:
            # 交易失败
            logger.error("支付失败:"+str( doc['xml']['return_msg']))
            return ERROR, "支付失败"

             
    def unified_order(self, order_id, openid, amount, desc, mch_id=None, notify_url=None, profit_sharing=False,
                      expire_time=None, attach=None, goods_tag=None, detail=None, scene_info=None, currency='CNY'):
        """
        统一下单：小程序及网页支付
        openid 微信小程序用户唯一标识
        https://pay.weixin.qq.com/wiki/doc/apiv3/apis/chapter3_1_1.shtml
        """
        url_path = '/v3/pay/transactions/jsapi' 
        url = self.base_url + url_path 
        data = {
            'appid': self.app_id,
            'mchid': mch_id if mch_id is not None else self.mch_id,
            'description': desc,
            'out_trade_no': order_id,
            'notify_url': notify_url if notify_url is not None else self.notify_url,
             
            'amount': {
                'total': amount,
                'currency': currency
            },
            'payer': {
                'openid': openid
            }
        }
        
        if attach:
            data.update({'attach': attach})
        if expire_time:
            data.update({'time_expire': expire_time})
        if goods_tag:
            data.update({'goods_tag': goods_tag})
        if detail:
            data.update({'detail': detail})
        if scene_info:
            data.update({'scene_info': scene_info})

        signature = self._generate_request_sign(url_path=url_path, data=data)
        headers = {'Authorization': self._generate_auth_header(signature)}
        print(data)
        res = requests.post(url=url, json=data,
                            headers=headers, timeout=TIMEOUT).json()
        logger.debug(res)
        # 支付签名
        pay_sign = self._generate_pay_sign(
            app_id=self.app_id, package='prepay_id=' + res['prepay_id'])

        if self.md5: 
            """
            https://pay.weixin.qq.com/wiki/doc/api/wxa/wxa_api.php?chapter=7_7&index=3
            paySign = MD5(appId=wxd678efh567hg6787&nonceStr=5K8264ILTKCH16CQ2502SI8ZNMTM67VS&package=prepay_id=wx2017033010242291fcfe0db70013231072&signType=MD5&timeStamp=1490840662&key=qazwsxedcrfvtgbyhnujmikolp111111) = 22D9B4E54AB1950F51E0649E8810ACD6
            """ 
            # 微信小程序
            return { 
                "provider": 'wxpay',
                "timeStamp": self.timestamp,
                "nonceStr": self.nonce_str,
                "package": 'prepay_id=' + res['prepay_id'],
                "signType": 'RSA',
                "paySign": pay_sign
            } 
        else: 
            return {
                'timestamp': self.timestamp,
                'nonce_str': self.nonce_str,
                'prepay_id': res['prepay_id'],
                'sign_type': 'RSA',
                'pay_sign': pay_sign
            }

    def unified_order_app(self, order_id,   amount, desc, mch_id=None, profit_sharing=False,
                          expire_time=None, attach=None, goods_tag=None, detail=None, scene_info=None, currency='CNY'):
        """
        统一下单APP 支付
        https://pay.weixin.qq.com/wiki/doc/apiv3/apis/chapter3_2_1.shtml
        """
        url_path = '/v3/pay/transactions/app'
        url = self.base_url + url_path

        data = {
            'appid': self.app_id,
            'mchid': mch_id if mch_id is not None else self.mch_id,
            'description': desc,
            'out_trade_no': order_id,
            'notify_url': self.notify_url,
            'settle_info': {
                'profit_sharing': profit_sharing
            },
            'amount': {
                'total': amount,
                'currency': currency
            },
        }

        if attach:
            data.update({'attach': attach})
        if expire_time:
            data.update({'time_expire': expire_time})
        if goods_tag:
            data.update({'goods_tag': goods_tag})
        if detail:
            data.update({'detail': detail})
        if scene_info:
            data.update({'scene_info': scene_info})

        signature = self._generate_request_sign(url_path=url_path, data=data)
        headers = {'Authorization': self._generate_auth_header(signature)}

        res = requests.post(url=url, json=data,
                            headers=headers, timeout=TIMEOUT).json()
        logger.debug(str(res))
        

        # 支付签名
        pay_sign = self._generate_pay_sign(
            app_id=self.app_id, package='prepay_id=' + res['prepay_id'])
        
        
        return {
            'timestamp': self.timestamp,
            'nonce_str': self.nonce_str,
            'prepay_id': res['prepay_id'],
            'sign_type': 'RSA',
            'pay_sign': pay_sign
        }

    def checkBillStatus(self, out_trade_no):
        # 查询out_trade_no的订单状态(商户订单号查询)
        # API说明 https://pay.weixin.qq.com/wiki/doc/apiv3/apis/chapter3_2_2.shtml
        # 返回查询结果
        url_path = '/v3/pay/transactions/out-trade-no/' + \
            out_trade_no + "?mchid="+self.mch_id
        apiurl = self.base_url + url_path

        signature = self._generate_request_sign(
            url_path=url_path, data=None, method="GET")
        headers = {'Authorization': self._generate_auth_header(signature)}
        req = requests.get(url=apiurl, headers=headers, timeout=TIMEOUT)
        result = {
            "status": ERROR
        } 
        if req.status_code == 200:
            #
            result['status'] = SUCCESS
            result['msg'] = json.loads(req.content)
        else:
            logger.error(req.content)
            result['msg'] = "获取微信支付订单状态失败"

        return result
    
    def checkSubBillStatus(self, out_trade_no):
        # 查询子商户的订单状态
        # 查询out_trade_no的订单状态(商户订单号查询)
        # API说明 https://pay.weixin.qq.com/wiki/doc/apiv3/apis/chapter3_2_2.shtml
        # 返回查询结果
        url_path = '/v3/pay/transactions/out-trade-no/' + \
            out_trade_no + "?mchid="+self.mch_id
        apiurl = self.base_url + url_path

        signature = self._generate_request_sign(
            url_path=url_path, data=None, method="GET")
        headers = {'Authorization': self._generate_auth_header(signature)}
        req = requests.get(url=apiurl, headers=headers, timeout=TIMEOUT)
        result = {
            "status": ERROR
        }
        if req.status_code == 200:
            #
            result['status'] = SUCCESS
            result['msg'] = json.loads(req.content)
        else:
            logger.error(req.content)
            result['msg'] = "获取微信支付订单状态失败"

        return result