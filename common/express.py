import requests, sys
import json, pdb
import pdb 


def get_express(no):
    """
    顺丰快递必须加手机号码后四位：
    快递单号错误, 顺丰快递必须添加收或寄件人手机尾号4位(单号:4位手机号)。例如：SF12345678:0123'
    快递查询：https://market.aliyun.com/products/57126001/cmapi021863.html?spm=5176.730005.result.2.64b3123eNHgL1Y&innerSource=search_%E5%BF%AB%E9%80%92%E7%89%A9%E6%B5%81%E6%9F%A5%E8%AF%A2#sku=yuncode1586300000
    {
	"status": "0",/* status 0:正常查询 201:快递单号错误 203:快递公司不存在 204:快递公司识别失败 205:没有信息 207:该单号被限制，错误单号 */
	"msg": "ok",
	"result": {
		"number": "780098068058",
		"type": "zto",
		"list": [{
			"time": "2018-03-09 11:59:26",
			"status": "【石家庄市】快件已在【长安三部】 签收,签收人: 本人,感谢使用中通快递,期待再次为您服务!"
		}, {
			"time": "2018-03-09 09:03:10",
			"status": "【石家庄市】 快件已到达 【长安三部】（0311-85344265）,业务员 容晓光（13081105270） 正在第1次派件, 请保持电话畅通,并耐心等待"
		}, {
			"time": "2018-03-08 23:43:44",
			"status": "【石家庄市】 快件离开 【石家庄】 发往 【长安三部】"
		}, {
			"time": "2018-03-08 21:00:44",
			"status": "【石家庄市】 快件到达 【石家庄】"
		}, {
			"time": "2018-03-07 01:38:45",
			"status": "【广州市】 快件离开 【广州中心】 发往 【石家庄】"
		}, {
			"time": "2018-03-07 01:36:53",
			"status": "【广州市】 快件到达 【广州中心】"
		}, {
			"time": "2018-03-07 00:40:57",
			"status": "【广州市】 快件离开 【广州花都】 发往 【石家庄中转】"
		}, {
			"time": "2018-03-07 00:01:55",
			"status": "【广州市】 【广州花都】（020-37738523） 的 马溪 （18998345739） 已揽收"
		}],
		"deliverystatus": "3", /* 0：快递收件(揽件)1.在途中 2.正在派件 3.已签收 4.派送失败 5.疑难件 6.退件签收  */
		"issign": "1",                      /*  1.是否签收                  */
		"expName": "中通快递",              /*  快递公司名称                */       
		"expSite": "www.zto.com",           /*  快递公司官网                */
		"expPhone": "95311",                /*  快递公司电话                */
		"courier": "容晓光",                /*  快递员 或 快递站(没有则为空)*/
        "courierPhone":"13081105270",       /*  快递员电话 (没有则为空)     */
        "updateTime":"2019-08-27 13:56:19", /*  快递轨迹信息最新时间        */
        "takeTime":"2天20小时14分",         /*  发货到收货消耗时长 (截止最新轨迹)  */
        "logo":"https://img3.fegine.com/express/zto.jpg" /* 快递公司LOGO */
	}
}
    """
    host = 'https://wuliu.market.alicloudapi.com/kdi'
    
    appcode = "b8da29c7215347d4b46581b54980b5c5"  
      
    querys = 'no='+no 
    url = host  + '?' + querys
    headers = {'Authorization': 'APPCODE ' + appcode}
    req = requests.get(url,headers=headers )  
    if req.status_code == 200:
        # 成功返回， 
        content = req.json()
        if content['status'] == "0":
            # 正常
            return 0, content['result']
        else:
            return 1, content['msg']
    else:
        return 1, "快递接口返回失败"
     
     
 