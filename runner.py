import requests
import time
import pdb
import json


DEBUG = False
if DEBUG:
    HOST = 'http://127.0.0.1:8000/api'
else:
    HOST = 'https://shopdemo.chidict.com/api' 

def initDb():
    """
    初始化数据库
    """
    # 1 初始化角色：默认角色：物业、业主、租户
    role_json =[
        ["物业", 2,   "wuye",  0],
        ["业主", 2,  "yezhu",  0],
        ["租户", 2,  "zuhu",  0]
    ]
    pyload = {"role": json.dumps(role_json)}
    result = requests.post(url=HOST + '/role/init/',
    data=pyload,
    headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}) 
    print(result)

def updateMoney():
    # 更新小区的总余额、总收入、总支出、总提现、短信剩余量等 
    result = requests.post(url=HOST + '/community/stat/',
    data={'analysis':''},
    headers={'Content-Type':'application/x-www-form-urlencoded'}) 
    print(result)


def updateFee():
    # 更新物业费缴费信息, 每天执行一次 
    result = requests.post(url=HOST + '/building/cal/', 
                            headers={'Content-Type':'application/x-www-form-urlencoded'}) 
    print(result)


def updateFeeRate():
    # 更新物业费缴费率，每个季度更新一次
    # 功能待完成
    result = requests.post(url=HOST + '/xxxx/xxxxx/',
    data={'analysis':''},
    headers={'Content-Type':'application/x-www-form-urlencoded'}) 
    print(result)

def createRecord():
    """
    定时创建登记薄功能
    未完成。
    """
    result = requests.post(url=HOST + '/xxxx/xxxxx/',
    data={'analysis':''},
    headers={'Content-Type':'application/x-www-form-urlencoded'}) 
    print(result)

def cancelBill():
    """
    超时取消订单
    """
    result = requests.post(url=HOST + '/bills/cancel/',
    data={ },
    headers={'Content-Type':'application/x-www-form-urlencoded'}) 
    print(result)

if __name__ == "__main__":
    counter = 0 
    while True: 
        cancelBill() 
        time.sleep(60 * 1) # 5分钟刷新一次
        counter += 1
        if counter == 12 * 12: # 12小时更新一次批量发送短信
            pass

        if counter == 12 * 24 : # 一天更新一次任务状态
            pass
            counter = 0
       
        

        