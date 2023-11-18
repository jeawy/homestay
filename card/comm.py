###################################
# 订单支付后， 购物卡的绑定、激活
###################################
from card.models import Card
import uuid
from datetime import datetime
from card.models import Card
from django.db.models import Sum
from bills.models import PayCards


def reduce_money(user, money, bill):
    # 使用余额支付 
    left = get_left_money(user)
    if left < money:
        return 1, "余额不足"
    else:
        if user.islooked == 0:
            user.islooked = 1
            user.save() # 锁定用户
            kwargs = {}
            kwargs['user'] = user
            kwargs['status'] = Card.ACTIVATED 
            kwargs['left__gt'] = 0 
            cards = Card.objects.filter(**kwargs).order_by("id")
            for card in cards:
                if card.left > money:
                    PayCards.objects.create(bill = bill, card=card, money=money)
                    card.left = card.left - money
                    card.save()
                    user.islooked = 0
                    user.save() # 解锁用户 
                    return 0, "已支付"
                else: 
                    money = money - card.left  
                    PayCards.objects.create(bill = bill, card=card, money=card.left  )
                    card.left = 0 # 已用完
                    card.save() 
                
                if money == 0:
                    user.islooked = 0
                    user.save() # 解锁用户 
                    return 0, "已支付" 
        else:
            return 2, "用户已锁定, 请等待"


def get_left_money(user):
    # 获取某个用户的购物卡余额
    kwargs = {}
    kwargs['user'] = user
    kwargs['status'] = Card.ACTIVATED 
    left = Card.objects.filter(**kwargs).aggregate(Sum("left"))['left__sum']  
    return left


def get_card_bind(bill, card):
    # 订单支付后， 购物卡的售卖
    pass

def create_card(money, cardtype):
    card = Card() 
    card.uuid = str(uuid.uuid4())
    card.money = money
    card.cardtype = cardtype
    card.money = money
    card.status = card.SALLED
    card.saledate = datetime.now()
    password = str(uuid.uuid4()).replace("-", "").upper()[4:16]
    while True:
        try:
            Card.objects.get(password = password)
        except Card.DoesNotExist: 
            card.password = password
            break
     
    card.save()
    return card