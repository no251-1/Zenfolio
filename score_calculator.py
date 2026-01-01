"""
客观评分计算模块
根据交易结果计算客观评分
"""
from typing import Optional
from models import ACTION_TYPES


def calculate_objective_score(
    action_type: str,
    buy_price: float,
    sell_price: float,
    buy_date: str,
    sell_date: Optional[str] = None
) -> int:
    """
    根据交易结果计算客观评分
    
    参数:
        action_type: 动作类型
        buy_price: 买入价格
        sell_price: 卖出价格（如果未卖出，使用当前价格）
        buy_date: 买入日期
        sell_date: 卖出日期（可选）
    
    返回:
        客观评分 (0-100)
    """
    if buy_price <= 0:
        return 0
    
    # 计算收益率
    profit_rate = (sell_price - buy_price) / buy_price * 100
    
    # 根据动作类型计算评分
    action_info = ACTION_TYPES.get(action_type, {})
    max_score = action_info.get("max_score", 20)
    
    if action_type == "涨了舍得卖":
        # 浮盈场景：盈利越多，评分越高
        # 盈利 >= 5%: 满分，盈利 0-5%: 线性评分，亏损: 0分
        if profit_rate >= 5:
            score = max_score
        elif profit_rate >= 0:
            score = int(max_score * (profit_rate / 5))
        else:
            score = 0
    
    elif action_type == "跌了敢买":
        # 浮亏场景：在下跌时买入，后续盈利越多评分越高
        # 盈利 >= 10%: 满分，盈利 0-10%: 线性评分，亏损: 0分
        if profit_rate >= 10:
            score = max_score
        elif profit_rate >= 0:
            score = int(max_score * (profit_rate / 10))
        else:
            score = 0
    
    elif action_type == "涨了敢买":
        # 突破场景：追涨成功评分高
        # 盈利 >= 8%: 满分，盈利 0-8%: 线性评分，亏损: 0分
        if profit_rate >= 8:
            score = max_score
        elif profit_rate >= 0:
            score = int(max_score * (profit_rate / 8))
        else:
            score = 0
    
    elif action_type == "跌了舍得卖":
        # 破位场景：及时止损评分高
        # 亏损 <= -5%: 满分（及时止损），亏损 -5% 到 0%: 线性递减，盈利: 满分
        if profit_rate >= 0:
            score = max_score  # 盈利说明判断正确
        elif profit_rate <= -5:
            score = max_score  # 及时止损
        else:
            # 亏损在 -5% 到 0% 之间，线性递减
            score = int(max_score * (1 + profit_rate / 5))
    
    else:
        score = 0
    
    # 确保评分在 0-100 范围内
    return max(0, min(100, score))

