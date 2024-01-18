import time
import pdb

def get_content(coupon):
    content = ""
    if coupon.coupontype == coupon.DISCOUNT:
        content = str(coupon.discount) + "折"
    else:
        content =  "满" + str(coupon.top_money) + "元, 减" + str(coupon.reduce_money) + "元"
    return content


def get_dict(coupon):
    coupon_dict = {
        "uuid":coupon.uuid,
        "date":time.mktime(coupon.date.timetuple()),
        "name":coupon.name,
        "status":coupon.status,
        "coupontype":coupon.coupontype,
        "start":time.mktime(coupon.start.timetuple()),
        "end":time.mktime(coupon.end.timetuple()), 
        "rules":coupon.rules,
        "limit":coupon.limit,
        "content" : get_content(coupon),
        "discount":coupon.discount,
        "top_money":coupon.top_money,
        "reduce_money":coupon.reduce_money,
        "extras" :coupon.extras
    }  
    coupon_dict['categories'] = list( coupon.categories.all().values("id", "name") )
    return coupon_dict