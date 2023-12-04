

def get_content(coupon):
    content = ""
    if coupon.coupontype == coupon.DISCOUNT:
        content = str(coupon.discount) + "折"
    else:
        content =  "满" + str(coupon.top_money) + "元, 减" + str(coupon.reduce_money) + "元"
    return content
