"""
数据模型定义
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Trade:
    """交易记录数据模型 - 支持交易周期"""
    id: Optional[int] = None
    trade_group_id: Optional[int] = None  # 同一笔交易的买入和卖出关联ID
    stock_code: Optional[str] = None
    stock_name: Optional[str] = None
    action_type: Optional[str] = None  # 4种动作类型之一（买入时的动作类型）
    trade_type: Optional[str] = None  # "买入" 或 "卖出"
    buy_date: Optional[str] = None  # 买入日期
    sell_date: Optional[str] = None  # 卖出日期（如果已卖出）
    buy_price: Optional[float] = None  # 买入价格
    sell_price: Optional[float] = None  # 卖出价格（如果已卖出）
    quantity: Optional[int] = None  # 交易数量
    status: Optional[str] = "进行中"  # "进行中" 或 "已结束"
    notes: Optional[str] = None


@dataclass
class Score:
    """评分记录数据模型 - 支持主观和客观评分"""
    id: Optional[int] = None
    trade_id: Optional[int] = None  # 关联的交易ID
    date: Optional[str] = None
    action_type: Optional[str] = None  # 4种动作类型之一
    score_type: Optional[str] = None  # "主观评分" 或 "客观评分"
    score: Optional[int] = None  # 0-100
    answer: Optional[str] = None  # 自检问题答案（仅主观评分）
    reflection: Optional[str] = None  # 反思笔记（仅主观评分）


# 动作类型定义
ACTION_TYPES = {
    "涨了舍得卖": {
        "description": "浮盈场景，克服贪婪",
        "max_score": 30,
        "question": "今天如果收盘盈利≥X%，我是否愿意按计划减仓？"
    },
    "跌了敢买": {
        "description": "浮亏场景，克服恐惧",
        "max_score": 30,
        "question": "如果价格再跌Y%，我是否还有现金、有勇气加仓？"
    },
    "涨了敢买": {
        "description": "突破/趋势延续，克服\"恐高\"",
        "max_score": 20,
        "question": "突破前高时，我是否敢用小仓位追趋势？"
    },
    "跌了舍得卖": {
        "description": "破位/逻辑破坏，克服\"惜亏\"",
        "max_score": 20,
        "question": "跌到止损位时，我能否立刻砍仓，不找理由？"
    }
}

