from datetime import datetime, timedelta
from paidservice.models import PaidOrder


def deleteUnpayedBills():
    # 自动删除超过指定期限还未支付的订单
    now = datetime.now()

    # 删除所有超过一天未支付的有偿服务订单
    PaidOrder.objects.filter(status = PaidOrder.NON_PAYMENT,
                             date__lte = now - timedelta(days=1)).delete()


