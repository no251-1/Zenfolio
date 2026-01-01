"""
数据可视化模块
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Optional
from database import Database
from models import ACTION_TYPES


def plot_score_trend(db: Database, start_date: Optional[str] = None, end_date: Optional[str] = None, score_type: Optional[str] = None) -> go.Figure:
    """
    绘制评分趋势折线图
    显示4个维度的评分随时间的变化
    """
    if start_date and end_date:
        df = db.get_scores_by_date_range(start_date, end_date, score_type)
    else:
        scores = db.get_all_scores(score_type=score_type)
        df = pd.DataFrame(scores)
    
    if df.empty:
        # 返回空图表
        fig = go.Figure()
        fig.add_annotation(
            text="暂无评分数据",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        return fig
    
    # 转换日期格式
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # 创建折线图
    fig = go.Figure()
    
    # 为每个动作类型绘制一条线
    colors = {
        "涨了舍得卖": "#FF6B6B",
        "跌了敢买": "#4ECDC4",
        "涨了敢买": "#FFE66D",
        "跌了舍得卖": "#95E1D3"
    }
    
    # 如果有评分类型，区分显示
    if 'score_type' in df.columns:
        for action_type in ACTION_TYPES.keys():
            action_df = df[df['action_type'] == action_type]
            if not action_df.empty:
                # 主观评分用实线
                subjective_df = action_df[action_df['score_type'] == '主观评分']
                if not subjective_df.empty:
                    fig.add_trace(go.Scatter(
                        x=subjective_df['date'],
                        y=subjective_df['score'],
                        mode='lines+markers',
                        name=f"{action_type} (主观)",
                        line=dict(color=colors.get(action_type, "#000000"), width=2, dash='solid'),
                        marker=dict(size=8),
                        hovertemplate=f'<b>{action_type} (主观)</b><br>' +
                                    '日期: %{x}<br>' +
                                    '评分: %{y}<br>' +
                                    '<extra></extra>'
                    ))
                
                # 客观评分用虚线
                objective_df = action_df[action_df['score_type'] == '客观评分']
                if not objective_df.empty:
                    fig.add_trace(go.Scatter(
                        x=objective_df['date'],
                        y=objective_df['score'],
                        mode='lines+markers',
                        name=f"{action_type} (客观)",
                        line=dict(color=colors.get(action_type, "#000000"), width=2, dash='dash'),
                        marker=dict(size=8, symbol='diamond'),
                        hovertemplate=f'<b>{action_type} (客观)</b><br>' +
                                    '日期: %{x}<br>' +
                                    '评分: %{y}<br>' +
                                    '<extra></extra>'
                    ))
    else:
        # 兼容旧数据
        for action_type in ACTION_TYPES.keys():
            action_df = df[df['action_type'] == action_type]
            if not action_df.empty:
                fig.add_trace(go.Scatter(
                    x=action_df['date'],
                    y=action_df['score'],
                    mode='lines+markers',
                    name=action_type,
                    line=dict(color=colors.get(action_type, "#000000"), width=2),
                    marker=dict(size=8),
                    hovertemplate=f'<b>{action_type}</b><br>' +
                                '日期: %{x}<br>' +
                                '评分: %{y}<br>' +
                                '<extra></extra>'
                ))
    
    title = "评分趋势图"
    if score_type:
        title += f" ({score_type})"
    
    fig.update_layout(
        title=title,
        xaxis_title="日期",
        yaxis_title="评分",
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=500
    )
    
    return fig


def plot_score_distribution(db: Database, score_type: Optional[str] = None) -> go.Figure:
    """
    绘制评分分布柱状图
    显示各动作类型的平均分、最高分、最低分
    """
    df = db.get_scores_summary(score_type=score_type)
    
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="暂无评分数据",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        return fig
    
    # 创建分组柱状图
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='平均分',
        x=df['action_type'],
        y=df['avg_score'],
        marker_color='#4ECDC4',
        text=df['avg_score'].round(1),
        textposition='outside'
    ))
    
    fig.add_trace(go.Bar(
        name='最高分',
        x=df['action_type'],
        y=df['max_score'],
        marker_color='#95E1D3',
        text=df['max_score'],
        textposition='outside'
    ))
    
    fig.add_trace(go.Bar(
        name='最低分',
        x=df['action_type'],
        y=df['min_score'],
        marker_color='#FF6B6B',
        text=df['min_score'],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="评分分布统计",
        xaxis_title="动作类型",
        yaxis_title="评分",
        barmode='group',
        height=400
    )
    
    return fig


def plot_score_radar(db: Database, score_type: Optional[str] = None) -> go.Figure:
    """
    绘制行为雷达图（用于复盘）
    显示各维度的平均分
    """
    df = db.get_scores_summary(score_type=score_type)
    
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="暂无评分数据",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        return fig
    
    # 准备雷达图数据
    categories = df['action_type'].tolist()
    values = df['avg_score'].tolist()
    
    # 闭合图形
    categories += [categories[0]]
    values += [values[0]]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='平均评分',
        line_color='#4ECDC4',
        fillcolor='rgba(78, 205, 196, 0.3)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickmode='linear',
                tick0=0,
                dtick=20
            )),
        showlegend=True,
        title="行为雷达图（复盘用）",
        height=500
    )
    
    return fig


def plot_daily_score_gauge(total_score: int, max_score: int = 100) -> go.Figure:
    """
    绘制今日总分仪表盘（进度环/仪表盘）
    """
    score_ratio = total_score / max_score if max_score > 0 else 0
    
    # 根据分数区间确定颜色和文案
    if total_score >= 85:
        color = "#00C853"  # 绿色
        feedback = "纪律碾压市场"
    elif total_score >= 70:
        color = "#4ECDC4"  # 青色
        feedback = "合格执行"
    elif total_score >= 50:
        color = "#FFE66D"  # 黄色
        feedback = "情绪干扰明显"
    else:
        color = "#FF6B6B"  # 红色
        feedback = "今日不适合重仓"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=total_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"今日交易执行力<br><span style='font-size:0.8em;color:gray'>{feedback}</span>"},
        delta={'reference': 70, 'position': "top"},
        gauge={
            'axis': {'range': [None, max_score]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 70], 'color': "gray"},
                {'range': [70, 85], 'color': "lightgreen"},
                {'range': [85, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 70
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig


def plot_trade_timeline(trades: List[Dict]) -> go.Figure:
    """
    绘制交易记录时间线
    """
    if not trades:
        fig = go.Figure()
        fig.add_annotation(
            text="暂无交易记录",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        return fig
    
    df = pd.DataFrame(trades)
    if 'buy_date' in df.columns:
        df['date'] = pd.to_datetime(df['buy_date'])
    elif 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    else:
        df['date'] = pd.to_datetime(df.get('created_at', pd.Timestamp.now()))
    df = df.sort_values('date')
    
    # 按动作类型分组
    colors = {
        "涨了舍得卖": "#FF6B6B",
        "跌了敢买": "#4ECDC4",
        "涨了敢买": "#FFE66D",
        "跌了舍得卖": "#95E1D3"
    }
    
    fig = go.Figure()
    
    for action_type in ACTION_TYPES.keys():
        action_df = df[df['action_type'] == action_type]
        if not action_df.empty:
            fig.add_trace(go.Scatter(
                x=action_df['date'],
                y=[action_type] * len(action_df),
                mode='markers',
                name=action_type,
                marker=dict(
                    size=10,
                    color=colors.get(action_type, "#000000")
                ),
                hovertemplate=f'<b>{action_type}</b><br>' +
                            '日期: %{x}<br>' +
                            '股票: %{customdata[0]} (%{customdata[1]})<br>' +
                            '价格: %{customdata[2]}<br>' +
                            '<extra></extra>',
                customdata=action_df[['stock_name', 'stock_code', 'buy_price']].values if 'buy_price' in action_df.columns else action_df[['stock_name', 'stock_code', 'price']].values
            ))
    
    fig.update_layout(
        title="交易记录时间线",
        xaxis_title="日期",
        yaxis_title="动作类型",
        height=400
    )
    
    return fig
