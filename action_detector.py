"""
根据股票走势自动判断动作类型
"""
from typing import Optional
from datetime import datetime, timedelta
import pandas as pd
from tushare_client import TushareClient


def detect_buy_action_type(
    tushare_client: TushareClient,
    stock_code: str,
    buy_date: str,
    buy_price: float,
    days_to_check: int = 5
) -> Optional[str]:
    """
    根据买入后的股票走势判断买入动作类型
    
    参数:
        tushare_client: tushare客户端
        stock_code: 股票代码
        buy_date: 买入日期 (YYYY-MM-DD)
        buy_price: 买入价格
        days_to_check: 检查后续几个交易日（默认5个）
    
    返回:
        "涨了敢买" 或 "跌了敢买" 或 None（如果无法判断）
    """
    if not tushare_client.is_configured():
        return None
    
    try:
        # 计算结束日期（买入日期 + 交易日数）
        buy_dt = datetime.strptime(buy_date, "%Y-%m-%d")
        end_dt = buy_dt + timedelta(days=days_to_check * 2)  # 预留非交易日
        
        # 获取买入日期之后的价格数据
        daily_data = tushare_client.get_stock_daily(
            stock_code,
            buy_date,
            end_dt.strftime("%Y-%m-%d")
        )
        
        if daily_data is None or daily_data.empty:
            return None
        
        # 过滤掉买入日期当天的数据，只看后续交易日
        buy_dt_only = buy_dt.date()
        future_data = daily_data[daily_data['trade_date'].dt.date > buy_dt_only]
        
        if future_data.empty:
            return None
        
        # 取前N个交易日
        future_data = future_data.head(days_to_check)
        
        if future_data.empty:
            return None
        
        # 计算平均收盘价（或者最后一个交易日的收盘价）
        avg_close = future_data['close'].mean()
        last_close = future_data['close'].iloc[-1]
        
        # 判断走势：如果后续价格高于买入价格，说明是"涨了敢买"
        # 如果后续价格低于买入价格，说明是"跌了敢买"
        if last_close > buy_price * 1.01:  # 考虑1%的误差
            return "涨了敢买"
        elif last_close < buy_price * 0.99:  # 考虑1%的误差
            return "跌了敢买"
        else:
            # 如果价格变化不大，根据平均价格判断
            if avg_close > buy_price:
                return "涨了敢买"
            else:
                return "跌了敢买"
    
    except Exception as e:
        print(f"判断买入动作类型失败: {e}")
        return None


def detect_sell_action_type(
    buy_price: float,
    sell_price: float,
    buy_date: str,
    sell_date: Optional[str] = None
) -> Optional[str]:
    """
    根据买入价格和卖出价格判断卖出动作类型
    
    参数:
        buy_price: 买入价格
        sell_price: 卖出价格
        buy_date: 买入日期
        sell_date: 卖出日期（可选）
    
    返回:
        "涨了舍得卖" 或 "跌了舍得卖" 或 None（如果无法判断）
    """
    if buy_price <= 0 or sell_price <= 0:
        return None
    
    # 计算涨跌幅度
    profit_rate = (sell_price - buy_price) / buy_price
    
    # 如果卖出价格高于买入价格，说明是"涨了舍得卖"
    # 如果卖出价格低于买入价格，说明是"跌了舍得卖"
    if profit_rate > 0.01:  # 盈利超过1%
        return "涨了舍得卖"
    elif profit_rate < -0.01:  # 亏损超过1%
        return "跌了舍得卖"
    else:
        # 如果变化不大，根据价格大小判断
        if sell_price > buy_price:
            return "涨了舍得卖"
        else:
            return "跌了舍得卖"

