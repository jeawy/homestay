###########
# 统计功能：
# 统计本小区物业的余额、今日收入、短信剩余量等
###########
from msg.comm import get_msg_left
from incomes.comm import statisticsMoneyOrg


def community_statatics(community):
    # 短信及账户金额变更的时候，应该调用这个接口进行更新
    # 统计本小区物业的余额、今日收入、短信剩余量等

    # 统计短信余额
    msg_left = get_msg_left(community)
    community.msg_left = msg_left

    # 统计总余额
    # 统计今日收入
    # 收入、支出(短信购买)、余额、今日收入
    income_total, expend_total, left, income_today = statisticsMoneyOrg(community)
    community.today_income_money = income_today
    community.money_left = left
    community.income_total = income_total 
    community.expend_total = expend_total 
    community.save()

    