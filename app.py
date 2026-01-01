"""
Streamlit 主应用
股票操作反思 Web App
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import Database
from models import Trade, Score, ACTION_TYPES
from tushare_client import TushareClient
from visualization import (
    plot_score_trend,
    plot_score_distribution,
    plot_score_radar,
    plot_trade_timeline,
    plot_daily_score_gauge
)
from score_calculator import calculate_objective_score
from action_detector import detect_buy_action_type, detect_sell_action_type
from config_manager import get_tushare_token, save_tushare_token

# 页面配置
st.set_page_config(
    page_title="股票操作反思",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化 session state
if 'db' not in st.session_state:
    st.session_state.db = Database()

if 'tushare_client' not in st.session_state:
    st.session_state.tushare_client = TushareClient()

# 从配置文件加载保存的 token
if 'tushare_token' not in st.session_state:
    saved_token = get_tushare_token()
    st.session_state.tushare_token = saved_token if saved_token else ""
    # 如果存在保存的 token，自动设置
    if saved_token:
        st.session_state.tushare_client.set_token(saved_token)

# 侧边栏配置
with st.sidebar:
    st.title("⚙️ 配置")
    
    # tushare token 配置
    st.subheader("tushare Token")
    
    if st.session_state.tushare_client.is_configured():
        st.success("✓ tushare 已配置")
        if st.session_state.tushare_token:
            st.caption(f"Token: {st.session_state.tushare_token[:10]}...")
        
        # 允许更新 token
        if st.button("🔄 更新 Token", key="update_token_btn"):
            st.session_state.show_token_input = True
        
        if st.session_state.get('show_token_input', False):
            token_input = st.text_input(
                "请输入新的 tushare token",
                type="password",
                help="在 tushare.pro 注册并获取 token",
                key="new_token_input"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 保存", key="save_token_btn"):
                    if token_input:
                        st.session_state.tushare_client.set_token(token_input)
                        st.session_state.tushare_token = token_input
                        save_tushare_token(token_input)
                        st.session_state.show_token_input = False
                        st.success("Token 已更新并保存")
                        st.rerun()
            with col2:
                if st.button("❌ 取消", key="cancel_token_btn"):
                    st.session_state.show_token_input = False
                    st.rerun()
    else:
        st.warning("⚠️ 请先配置 tushare token")
        token_input = st.text_input(
            "请输入您的 tushare token",
            value=st.session_state.tushare_token,
            type="password",
            help="在 tushare.pro 注册并获取 token",
            key="token_input"
        )
        
        if token_input and token_input != st.session_state.tushare_token:
            st.session_state.tushare_client.set_token(token_input)
            st.session_state.tushare_token = token_input
            save_tushare_token(token_input)  # 保存到配置文件
            st.success("Token 已保存")
            st.rerun()
    
    st.divider()
    
    # 数据管理
    st.subheader("数据管理")
    if st.button("导出数据"):
        trades = st.session_state.db.get_all_trades()
        scores = st.session_state.db.get_all_scores()
        
        if trades or scores:
            with pd.ExcelWriter("stock_reflection_data.xlsx", engine='openpyxl') as writer:
                if trades:
                    pd.DataFrame(trades).to_excel(writer, sheet_name='交易记录', index=False)
                if scores:
                    pd.DataFrame(scores).to_excel(writer, sheet_name='评分记录', index=False)
            st.success("数据已导出到 stock_reflection_data.xlsx")
        else:
            st.info("暂无数据可导出")
    
    st.divider()
    
    # 统计信息
    st.subheader("📊 统计")
    total_trades = len(st.session_state.db.get_all_trades())
    total_scores = len(st.session_state.db.get_all_scores())
    st.metric("交易记录", total_trades)
    st.metric("评分记录", total_scores)

# 主标题
st.title("📈 股票操作反思系统")
st.markdown("---")

# 主界面标签页
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 每日自检", "📝 买入交易", "💰 卖出交易", "📈 复盘分析", "📋 交易历史"])

# 标签页1: 每日自检（核心功能）
with tab1:
    st.title("📊 交易行为自律评分卡")
    st.caption("每日快速自检 + 强化行为反馈")
    
    # 获取今日日期
    today = datetime.now().strftime("%Y-%m-%d")
    buy_date = st.date_input("选择日期", value=datetime.now().date(), key="daily_date")
    selected_date = buy_date.strftime("%Y-%m-%d")
    
    # 初始化评分数据
    subjective_scores = {}
    answers = {}
    hardest_action = None
    
    # 计算今日总分（实时）
    def calculate_total_score(scores):
        return sum(scores.values())
    
    # 四张行为卡片
    st.markdown("---")
    st.subheader("四张行为卡片")
    
    # 为每个动作类型创建一张卡片
    for idx, (action_type_key, action_info) in enumerate(ACTION_TYPES.items()):
        with st.container():
            # 卡片样式
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # 卡片标题和说明
                st.markdown(f"### ① {action_type_key}  {action_info['max_score']}分")
                st.caption(f"**场景**: {action_info['description']}")
                st.markdown(f"**🎯 克服**: {action_info['description'].split('，')[1] if '，' in action_info['description'] else action_info['description']}")
                
                # 自检问题
                with st.expander("📋 自检问题", expanded=False):
                    st.write(action_info['question'])
                    answer = st.text_area(
                        "你的答案",
                        height=80,
                        key=f"daily_answer_{action_type_key}",
                        placeholder="记录你的思考和判断..."
                    )
                    answers[action_type_key] = answer
            
            with col2:
                # 执行度星级评分（5个等级）
                st.markdown("**执行度**")
                
                # 计算每个等级的分数
                max_score = action_info['max_score']
                level_score = max_score / 5  # 每个等级对应的分数
                
                # 初始化星级状态
                star_key = f"star_{action_type_key}"
                if star_key not in st.session_state:
                    st.session_state[star_key] = 0
                
                # 创建5个可点击的星星按钮（横向排列，紧凑布局）
                star_cols = st.columns([1, 1, 1, 1, 1])
                star_level = st.session_state[star_key]
                
                # 使用CSS美化按钮
                st.markdown("""
                <style>
                div[data-testid="column"] button {
                    font-size: 28px !important;
                    padding: 2px 4px !important;
                    min-height: 40px !important;
                    border-radius: 8px !important;
                }
                </style>
                """, unsafe_allow_html=True)
                
                for i in range(5):
                    with star_cols[i]:
                        star_num = i + 1
                        # 判断这颗星是否被选中
                        is_selected = star_num <= star_level
                        star_icon = "⭐" if is_selected else "☆"
                        
                        # 创建按钮，点击后更新星级
                        if st.button(
                            star_icon,
                            key=f"star_btn_{action_type_key}_{star_num}",
                            width='stretch',
                            help=f"{star_num}星 ({int(star_num * level_score)}分)"
                        ):
                            st.session_state[star_key] = star_num
                            star_level = star_num
                            st.rerun()
                
                # 根据星级计算分数
                score = int(star_level * level_score)
                subjective_scores[action_type_key] = score
                
                # 显示当前选择的星级和分数
                if star_level > 0:
                    stars_display = "⭐" * star_level + "☆" * (5 - star_level)
                    st.markdown(f"**{stars_display}**")
                    st.caption(f"**{score}/{max_score}分**")
                else:
                    st.markdown("**☆☆☆☆☆**")
                    st.caption(f"**0/{max_score}分**")
            
            st.markdown("---")
    
    # 今日最难的一条
    st.markdown("---")
    st.subheader("🧠 今日最难的一条")
    st.caption("今天哪一个动作，最违背我的本能？")
    hardest_action = st.radio(
        "选择最难的行动",
        options=["无"] + list(ACTION_TYPES.keys()),
        horizontal=True,
        key="hardest_action"
    )
    
    # 今日总分仪表盘
    st.markdown("---")
    total_score = calculate_total_score(subjective_scores)
    max_total_score = sum(v['max_score'] for v in ACTION_TYPES.values())  # 100分
    
    # 显示仪表盘
    fig_gauge = plot_daily_score_gauge(total_score, max_total_score)
    st.plotly_chart(
        fig_gauge, 
        config={"displayModeBar": False}, 
        width='stretch', 
        key="daily_gauge"
    )
    
    # 保存函数
    def save_daily_scores():
        """保存每日自检评分"""
        saved_count = 0
        for action_type_key, score in subjective_scores.items():
            if score > 0:
                score_record = Score(
                    trade_id=None,  # 每日自检不关联具体交易
                    date=selected_date,
                    action_type=action_type_key,
                    score_type="主观评分",
                    score=score,
                    answer=answers.get(action_type_key),
                    reflection=f"最难行动: {hardest_action}" if hardest_action != "无" else None
                )
                st.session_state.db.add_score(score_record)
                saved_count += 1
        
        if saved_count > 0:
            st.success(f"✓ 今日自检已保存！总分: {total_score}/{max_total_score}分")
            st.balloons()
        else:
            st.error("请至少对一个维度进行评分")
    
    # 保存按钮
    if st.button("💾 保存今日自检", type="primary", width='stretch', key="daily_submit"):
        if total_score == 0:
            st.warning("⚠️ 请至少对一个维度进行评分")
        else:
            # 检查是否已有今日记录
            today_scores = st.session_state.db.get_scores_by_date_range(selected_date, selected_date, "主观评分")
            
            # 检查 DataFrame 是否为空
            if not today_scores.empty:
                # 删除今日旧记录（自动覆盖）
                for _, old_score in today_scores.iterrows():
                    st.session_state.db.delete_score(old_score['id'])
                save_daily_scores()
            else:
                save_daily_scores()

# 标签页2: 买入交易
with tab2:
    st.header("记录买入交易")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 交易信息
        st.subheader("买入信息")
        buy_date = st.date_input("买入日期", value=datetime.now().date(), key="buy_date")
        stock_code = st.text_input("股票代码", placeholder="例如: 000001 或 600000", help="输入6位股票代码")
        
        # 获取股票信息
        stock_info = None
        if stock_code and st.session_state.tushare_client.is_configured():
            if st.button("查询股票信息", type="primary", key="buy_query"):
                with st.spinner("正在查询..."):
                    stock_info = st.session_state.tushare_client.get_stock_basic_info(stock_code)
                    if stock_info:
                        st.session_state.stock_info_buy = stock_info
                        st.success(f"✓ 找到股票: {stock_info['name']}")
                    else:
                        st.error("未找到该股票，请检查代码是否正确")
        
        if 'stock_info_buy' in st.session_state:
            stock_info = st.session_state.stock_info_buy
            st.info(f"**{stock_info['name']}** ({stock_info['ts_code']})")
        
        stock_name = st.text_input("股票名称", value=stock_info['name'] if stock_info else "", key="buy_stock_name")
        
        buy_price = st.number_input("买入价格", min_value=0.0, format="%.2f", key="buy_price")
        quantity = st.number_input("买入数量", min_value=0, step=100, key="buy_quantity")
        notes = st.text_area("交易备注", height=100, key="buy_notes")
        
        # 动作类型自动判断
        action_type = None
        if stock_code and buy_price > 0 and buy_date:
            st.markdown("**动作类型（自动判断）**")
            if st.button("🔍 根据股票走势判断动作类型", key="detect_buy_action", type="secondary"):
                with st.spinner("正在分析股票走势..."):
                    action_type = detect_buy_action_type(
                        st.session_state.tushare_client,
                        stock_code,
                        buy_date.strftime("%Y-%m-%d"),
                        buy_price,
                        days_to_check=5
                    )
                    if action_type:
                        st.session_state.detected_buy_action = action_type
                        st.success(f"✓ 自动判断: **{action_type}**")
                    else:
                        st.warning("⚠️ 无法自动判断，请手动选择")
            
            if 'detected_buy_action' in st.session_state:
                action_type = st.session_state.detected_buy_action
                st.info(f"**当前判断**: {action_type}")
        
        # 如果无法自动判断，允许手动选择
        if not action_type:
            st.markdown("**动作类型（手动选择）**")
            action_type = st.radio(
                "选择动作类型",
                options=["涨了敢买", "跌了敢买"],
                horizontal=True,
                label_visibility="collapsed",
                key="buy_action_type"
            )
    
    with col2:
        # 买入时的主观评分（只显示买入相关的动作类型）
        st.subheader("买入时主观评分")
        st.info("💡 请对买入相关的维度打分")
        
        # 初始化评分数据
        buy_subjective_scores = {}
        buy_answers = {}
        
        # 买入时只显示买入相关的动作类型
        buy_action_types = {
            "跌了敢买": ACTION_TYPES["跌了敢买"],
            "涨了敢买": ACTION_TYPES["涨了敢买"]
        }
        
        # 为每个买入相关的动作类型创建星级评分
        for action_type_key, action_info in buy_action_types.items():
            st.markdown(f"**{action_type_key}** ({action_info['max_score']}分)")
            
            # 初始化星级状态
            star_key = f"buy_star_{action_type_key}"
            if star_key not in st.session_state:
                st.session_state[star_key] = 0
            
            # 创建5个可点击的星星按钮
            star_cols = st.columns([1, 1, 1, 1, 1])
            star_level = st.session_state[star_key]
            max_score = action_info['max_score']
            level_score = max_score / 5
            
            for i in range(5):
                with star_cols[i]:
                    star_num = i + 1
                    is_selected = star_num <= star_level
                    star_icon = "⭐" if is_selected else "☆"
                    
                    if st.button(
                        star_icon,
                        key=f"buy_star_btn_{action_type_key}_{star_num}",
                        width='stretch',
                        help=f"{star_num}星 ({int(star_num * level_score)}分)"
                    ):
                        st.session_state[star_key] = star_num
                        star_level = star_num
                        st.rerun()
            
            # 计算分数
            score = int(star_level * level_score)
            buy_subjective_scores[action_type_key] = score
            
            # 自检问题答案
            with st.expander(f"自检问题", expanded=False):
                st.caption(action_info['question'])
                answer = st.text_area(
                    "答案",
                    height=60,
                    key=f"buy_answer_{action_type_key}",
                    label_visibility="collapsed"
                )
                buy_answers[action_type_key] = answer
            
            st.markdown("---")
        
        # 总体反思
        buy_reflection = st.text_area("总体反思笔记", height=80, key="buy_reflection")
    
    # 提交按钮
    if st.button("💾 保存买入记录和评分", type="primary", width='stretch', key="buy_submit"):
        if not stock_code:
            st.error("请填写股票代码")
        elif not action_type:
            st.error("请先判断或选择动作类型")
        elif buy_price <= 0:
            st.error("请输入买入价格")
        elif quantity <= 0:
            st.error("请输入买入数量")
        else:
            # 如果还未判断，尝试自动判断
            if 'detected_buy_action' not in st.session_state or not st.session_state.detected_buy_action:
                if st.session_state.tushare_client.is_configured():
                    action_type = detect_buy_action_type(
                        st.session_state.tushare_client,
                        stock_code,
                        buy_date.strftime("%Y-%m-%d"),
                        buy_price
                    )
                    if action_type:
                        st.session_state.detected_buy_action = action_type
                else:
                    # 如果tushare未配置，使用手动选择的值
                    if action_type not in ["涨了敢买", "跌了敢买"]:
                        st.error("请配置tushare token以自动判断，或手动选择动作类型")
                        action_type = None
            
            if action_type:
                # 保存买入交易记录
                trade = Trade(
                    stock_code=stock_code,
                    stock_name=stock_name or stock_code,
                    action_type=action_type,
                    trade_type="买入",
                    buy_date=buy_date.strftime("%Y-%m-%d"),
                    buy_price=buy_price,
                    quantity=quantity,
                    status="进行中",
                    notes=notes if notes else None
                )
                trade_id = st.session_state.db.add_trade(trade)
                
                # 保存四象限主观评分
                saved_scores = []
                for action_type_key, score in buy_subjective_scores.items():
                    if score > 0:
                        score_record = Score(
                            trade_id=trade_id,
                            date=buy_date.strftime("%Y-%m-%d"),
                            action_type=action_type_key,
                            score_type="主观评分",
                            score=score,
                            answer=buy_answers.get(action_type_key),
                            reflection=buy_reflection if buy_reflection else None
                        )
                        st.session_state.db.add_score(score_record)
                        saved_scores.append(f"{action_type_key}: {score}分")
                
                if saved_scores:
                    st.success(f"✓ 买入记录和主观评分已保存！交易ID: {trade_id}")
                    st.info(f"动作类型: {action_type} | 已保存评分: {', '.join(saved_scores)}")
                else:
                    st.success(f"✓ 买入记录已保存！交易ID: {trade_id}")
                    st.info(f"动作类型: {action_type}")
                    st.warning("⚠️ 未记录任何主观评分")
                
                st.balloons()
                
                # 清除临时状态
                if 'stock_info_buy' in st.session_state:
                    del st.session_state.stock_info_buy
                if 'detected_buy_action' in st.session_state:
                    del st.session_state.detected_buy_action

# 标签页3: 卖出交易
with tab3:
    st.header("记录卖出交易")
    
    # 获取进行中的交易
    active_trades = st.session_state.db.get_active_trades()
    
    if not active_trades:
        st.info("暂无进行中的交易")
    else:
        # 选择要卖出的交易
        trade_options = {
            f"{t['stock_name']} ({t['stock_code']}) - {t['buy_date']} - {t['buy_price']}元": t['id']
            for t in active_trades
        }
        
        selected_trade_key = st.selectbox("选择要卖出的交易", options=list(trade_options.keys()))
        selected_trade_id = trade_options[selected_trade_key]
        selected_trade = next(t for t in active_trades if t['id'] == selected_trade_id)
        
        # 计算已卖出数量和剩余数量（在col定义之前，确保作用域正确）
        trade_group_id = selected_trade.get('trade_group_id', selected_trade['id'])
        sold_quantity = st.session_state.db.get_sold_quantity(trade_group_id)
        remaining_quantity = selected_trade['quantity'] - sold_quantity
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("卖出信息")
            st.info(f"**股票**: {selected_trade['stock_name']} ({selected_trade['stock_code']})")
            st.info(f"**买入日期**: {selected_trade['buy_date']}")
            st.info(f"**买入价格**: {selected_trade['buy_price']} 元")
            st.info(f"**买入数量**: {selected_trade['quantity']} 股")
            
            if sold_quantity > 0:
                st.info(f"**已卖出**: {sold_quantity} 股")
                st.info(f"**剩余可卖**: {remaining_quantity} 股")
            else:
                st.info(f"**剩余可卖**: {remaining_quantity} 股")
            
            sell_date = st.date_input("卖出日期", value=datetime.now().date(), key="sell_date")
            
            sell_quantity = st.number_input(
                "卖出数量", 
                min_value=1, 
                max_value=int(remaining_quantity) if remaining_quantity > 0 else 1,
                value=1,
                step=100,
                key="sell_quantity",
                help=f"最多可卖出 {remaining_quantity} 股"
            )
            sell_price = st.number_input("卖出价格", min_value=0.0, format="%.2f", key="sell_price")
            
            # 计算盈亏（基于本次卖出数量）
            if sell_price > 0 and selected_trade['buy_price'] > 0 and sell_quantity > 0:
                profit = (sell_price - selected_trade['buy_price']) * sell_quantity
                profit_rate = (sell_price - selected_trade['buy_price']) / selected_trade['buy_price'] * 100
                st.metric("本次盈亏金额", f"{profit:,.2f} 元", f"{profit_rate:.2f}%")
                
                # 如果是全部卖出，显示提示
                if sell_quantity == remaining_quantity:
                    st.success("🎯 本次将全部卖出")
                elif sell_quantity < remaining_quantity:
                    st.info(f"💡 本次卖出后剩余 {remaining_quantity - sell_quantity} 股")
        
        with col2:
            # 卖出时的主观评分（只显示卖出相关的动作类型）
            st.subheader("卖出时主观评分")
            st.info("💡 请对卖出相关的维度打分")
            
            # 初始化评分数据
            sell_subjective_scores = {}
            sell_answers = {}
            
            # 卖出时只显示卖出相关的动作类型
            sell_action_types = {
                "涨了舍得卖": ACTION_TYPES["涨了舍得卖"],
                "跌了舍得卖": ACTION_TYPES["跌了舍得卖"]
            }
            
            # 为每个卖出相关的动作类型创建星级评分
            for action_type_key, action_info in sell_action_types.items():
                st.markdown(f"**{action_type_key}** ({action_info['max_score']}分)")
                
                # 初始化星级状态
                star_key = f"sell_star_{action_type_key}"
                if star_key not in st.session_state:
                    st.session_state[star_key] = 0
                
                # 创建5个可点击的星星按钮
                star_cols = st.columns([1, 1, 1, 1, 1])
                star_level = st.session_state[star_key]
                max_score = action_info['max_score']
                level_score = max_score / 5
                
                for i in range(5):
                    with star_cols[i]:
                        star_num = i + 1
                        is_selected = star_num <= star_level
                        star_icon = "⭐" if is_selected else "☆"
                        
                        if st.button(
                            star_icon,
                            key=f"sell_star_btn_{action_type_key}_{star_num}",
                            width='stretch',
                            help=f"{star_num}星 ({int(star_num * level_score)}分)"
                        ):
                            st.session_state[star_key] = star_num
                            star_level = star_num
                            st.rerun()
                
                # 计算分数
                score = int(star_level * level_score)
                sell_subjective_scores[action_type_key] = score
                
                # 自检问题答案
                with st.expander(f"自检问题", expanded=False):
                    st.caption(action_info['question'])
                    answer = st.text_area(
                        "答案",
                        height=60,
                        key=f"sell_answer_{action_type_key}",
                        label_visibility="collapsed"
                    )
                    sell_answers[action_type_key] = answer
                
                st.markdown("---")
            
            # 总体反思
            sell_reflection = st.text_area("总体反思笔记", height=80, key="sell_reflection")
            
            # 自动判断卖出动作类型
            sell_action_type = None
            if sell_price > 0 and selected_trade['buy_price'] > 0:
                st.markdown("---")
                st.subheader("卖出动作类型（自动判断）")
                sell_action_type = detect_sell_action_type(
                    buy_price=selected_trade['buy_price'],
                    sell_price=sell_price,
                    buy_date=selected_trade['buy_date'],
                    sell_date=sell_date.strftime("%Y-%m-%d")
                )
                if sell_action_type:
                    st.session_state.detected_sell_action = sell_action_type
                    st.info(f"**自动判断**: {sell_action_type}")
                
                # 客观评分预览
                if sell_action_type:
                    objective_score = calculate_objective_score(
                        action_type=sell_action_type,
                        buy_price=selected_trade['buy_price'],
                        sell_price=sell_price,
                        buy_date=selected_trade['buy_date'],
                        sell_date=sell_date.strftime("%Y-%m-%d")
                    )
                    st.metric("客观评分", f"{objective_score} 分", help="根据交易结果自动计算")
        
        # 提交按钮
        if st.button("💾 保存卖出记录和评分", type="primary", width='stretch', key="sell_submit"):
            if sell_price <= 0:
                st.error("请输入卖出价格")
            elif sell_quantity <= 0:
                st.error("请输入卖出数量")
            elif sell_quantity > remaining_quantity:
                st.error(f"卖出数量不能超过剩余可卖数量 {remaining_quantity} 股")
            else:
                trade_group_id = selected_trade.get('trade_group_id', selected_trade['id'])
                
                # 保存卖出交易记录
                sell_trade = Trade(
                    trade_group_id=trade_group_id,
                    stock_code=selected_trade['stock_code'],
                    stock_name=selected_trade['stock_name'],
                    action_type=None,  # 卖出记录不存储动作类型
                    trade_type="卖出",
                    buy_date=selected_trade['buy_date'],
                    sell_date=sell_date.strftime("%Y-%m-%d"),
                    buy_price=selected_trade['buy_price'],
                    sell_price=sell_price,
                    quantity=sell_quantity,
                    status="已结束",  # 卖出记录总是已结束
                    notes=None
                )
                sell_trade_id = st.session_state.db.add_trade(sell_trade)
                
                # 检查并更新买入记录状态（如果全部卖出）
                st.session_state.db.update_trade_status(trade_group_id)
                
                # 获取卖出动作类型（如果还未判断，自动判断）
                if 'detected_sell_action' not in st.session_state or not st.session_state.detected_sell_action:
                    sell_action_type = detect_sell_action_type(
                        buy_price=selected_trade['buy_price'],
                        sell_price=sell_price,
                        buy_date=selected_trade['buy_date'],
                        sell_date=sell_date.strftime("%Y-%m-%d")
                    )
                else:
                    sell_action_type = st.session_state.detected_sell_action
                
                # 保存四象限主观评分（关联到卖出记录）
                saved_subjective_scores = []
                for action_type_key, score in sell_subjective_scores.items():
                    if score > 0:
                        score_record = Score(
                            trade_id=sell_trade_id,  # 关联到卖出记录
                            date=sell_date.strftime("%Y-%m-%d"),
                            action_type=action_type_key,
                            score_type="主观评分",
                            score=score,
                            answer=sell_answers.get(action_type_key),
                            reflection=sell_reflection if sell_reflection else None
                        )
                        st.session_state.db.add_score(score_record)
                        saved_subjective_scores.append(f"{action_type_key}: {score}分")
                
                # 计算并保存客观评分（使用自动判断的卖出动作类型）
                if sell_action_type:
                    objective_score = calculate_objective_score(
                        action_type=sell_action_type,
                        buy_price=selected_trade['buy_price'],
                        sell_price=sell_price,
                        buy_date=selected_trade['buy_date'],
                        sell_date=sell_date.strftime("%Y-%m-%d")
                    )
                    
                    score_record = Score(
                        trade_id=sell_trade_id,  # 关联到卖出记录
                        date=sell_date.strftime("%Y-%m-%d"),
                        action_type=sell_action_type,
                        score_type="客观评分",
                        score=objective_score,
                        answer=None,
                        reflection=None
                    )
                    score_id = st.session_state.db.add_score(score_record)
                else:
                    objective_score = 0
                    score_id = None
                
                # 判断是否全部卖出
                new_sold_quantity = sold_quantity + sell_quantity
                is_fully_sold = new_sold_quantity >= selected_trade['quantity']
                
                if saved_subjective_scores:
                    st.success(f"✓ 卖出记录、主观评分和客观评分已保存！")
                    if is_fully_sold:
                        st.info(f"🎯 已全部卖出 | 卖出动作类型: {sell_action_type} | 本次卖出: {sell_quantity}股 | 主观评分: {', '.join(saved_subjective_scores)} | 客观评分: {objective_score}分")
                    else:
                        st.info(f"💡 本次卖出: {sell_quantity}股，剩余: {remaining_quantity - sell_quantity}股 | 卖出动作类型: {sell_action_type} | 主观评分: {', '.join(saved_subjective_scores)} | 客观评分: {objective_score}分")
                else:
                    st.success(f"✓ 卖出记录和客观评分已保存！")
                    if is_fully_sold:
                        st.info(f"🎯 已全部卖出 | 卖出动作类型: {sell_action_type} | 本次卖出: {sell_quantity}股 | 客观评分: {objective_score}分")
                    else:
                        st.info(f"💡 本次卖出: {sell_quantity}股，剩余: {remaining_quantity - sell_quantity}股 | 卖出动作类型: {sell_action_type} | 客观评分: {objective_score}分")
                    st.warning("⚠️ 未记录任何主观评分")
                
                # 清除临时状态
                if 'detected_sell_action' in st.session_state:
                    del st.session_state.detected_sell_action
                
                st.balloons()
                st.rerun()

# 标签页4: 复盘分析
with tab4:
    st.title("📈 复盘分析")
    st.caption("周/月复盘用 - 发现行为模式与短板")
    
    # 日期范围选择
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("开始日期", value=datetime.now().date() - timedelta(days=30))
    with col2:
        end_date = st.date_input("结束日期", value=datetime.now().date())
    
    # 评分类型选择
    score_type_filter = st.radio(
        "选择评分类型",
        options=["主观评分", "客观评分", "全部"],
        horizontal=True,
        key="score_type_filter"
    )
    
    score_type = None if score_type_filter == "全部" else score_type_filter
    
    # 行为雷达图（核心复盘工具）
    st.markdown("---")
    st.subheader("🎯 行为雷达图")
    st.caption("一眼看出：你是「贪婪型 / 恐惧型 / 惜亏型」？哪个动作是长期短板？")
    
    fig_radar = plot_score_radar(st.session_state.db, score_type=score_type)
    st.plotly_chart(
        fig_radar, 
        config={"displayModeBar": False}, 
        width='stretch', 
        key="score_radar_chart"
    )
    
    # 评分趋势图
    st.markdown("---")
    st.subheader("📈 评分趋势图")
    fig_trend = plot_score_trend(
        st.session_state.db,
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d"),
        score_type=score_type
    )
    st.plotly_chart(
        fig_trend, 
        config={"displayModeBar": False}, 
        width='stretch', 
        key="score_trend_chart"
    )
    
    # 统计图表
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 评分分布")
        fig_dist = plot_score_distribution(st.session_state.db, score_type=score_type)
        st.plotly_chart(
            fig_dist, 
            config={"displayModeBar": False}, 
            width='stretch', 
            key="score_distribution_chart"
        )
    
    with col2:
        # 评分汇总表
        st.subheader("📋 评分汇总")
        summary_df = st.session_state.db.get_scores_summary(score_type=score_type)
        if not summary_df.empty:
            summary_df = summary_df.round(2)
            summary_df.columns = ['动作类型', '记录数', '平均分', '最低分', '最高分']
            st.dataframe(summary_df, width='stretch')
        else:
            st.info("暂无评分数据")
    
    # 最近评分记录
    st.markdown("---")
    st.subheader("📝 最近评分记录")
    recent_scores = st.session_state.db.get_all_scores(limit=20, score_type=score_type)
    if recent_scores:
        scores_df = pd.DataFrame(recent_scores)
        if 'score_type' in scores_df.columns:
            scores_df = scores_df[['date', 'action_type', 'score_type', 'score', 'answer', 'reflection']]
            scores_df.columns = ['日期', '动作类型', '评分类型', '评分', '自检答案', '反思']
        else:
            scores_df = scores_df[['date', 'action_type', 'score', 'answer', 'reflection']]
            scores_df.columns = ['日期', '动作类型', '评分', '自检答案', '反思']
        st.dataframe(scores_df, width='stretch')
    else:
        st.info("暂无评分记录")

# 标签页5: 交易历史
with tab5:
    st.header("交易历史记录")
    
    # 筛选选项
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_stock = st.text_input("🔍 搜索股票代码或名称", "")
    with col2:
        filter_action = st.selectbox("筛选动作类型", options=["全部"] + list(ACTION_TYPES.keys()))
    with col3:
        filter_status = st.selectbox("筛选状态", options=["全部", "进行中", "已结束"])
    
    # 获取交易组
    trade_groups = st.session_state.db.get_trade_groups()
    
    if trade_groups:
        df = pd.DataFrame(trade_groups)
        
        # 应用筛选
        if filter_stock:
            mask = (df['stock_code'].str.contains(filter_stock, case=False, na=False) |
                   df['stock_name'].str.contains(filter_stock, case=False, na=False))
            df = df[mask]
        
        if filter_action != "全部":
            df = df[df['action_type'] == filter_action]
        
        if filter_status != "全部":
            df = df[df['status'] == filter_status]
        
        # 排序
        df = df.sort_values('buy_date', ascending=False)
        
        # 计算盈亏
        if 'buy_price' in df.columns and 'sell_price' in df.columns:
            # 确保价格列为数值类型
            df['buy_price'] = pd.to_numeric(df['buy_price'], errors='coerce')
            df['sell_price'] = pd.to_numeric(df['sell_price'], errors='coerce')
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
            
            df['profit'] = (df['sell_price'] - df['buy_price']) * df['quantity']
            df['profit_rate'] = ((df['sell_price'] - df['buy_price']) / df['buy_price'] * 100).round(2)
        
        # 显示数据
        display_cols = ['buy_date', 'sell_date', 'stock_code', 'stock_name', 'action_type', 
                       'buy_price', 'sell_price', 'quantity', 'status']
        if 'profit' in df.columns:
            display_cols.extend(['profit', 'profit_rate'])
        
        display_df = df[[col for col in display_cols if col in df.columns]].copy()
        display_df.columns = ['买入日期', '卖出日期', '股票代码', '股票名称', '动作类型', 
                             '买入价', '卖出价', '数量', '状态'] + (['盈亏', '盈亏率%'] if 'profit' in df.columns else [])
        
        st.dataframe(display_df, width='stretch')
        
        # 统计信息
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总交易数", len(df))
        with col2:
            st.metric("进行中", len(df[df['status'] == '进行中']))
        with col3:
            st.metric("已结束", len(df[df['status'] == '已结束']))
        with col4:
            if 'profit' in df.columns and not df[df['status'] == '已结束']['profit'].isna().all():
                total_profit = df[df['status'] == '已结束']['profit'].sum()
                st.metric("总盈亏", f"{total_profit:,.2f} 元")
            else:
                st.metric("涉及股票数", df['stock_code'].nunique())
        
        # 交易时间线
        st.subheader("📅 交易时间线")
        all_trades = st.session_state.db.get_all_trades()
        fig_timeline = plot_trade_timeline(all_trades)
        st.plotly_chart(
            fig_timeline, 
            config={"displayModeBar": False}, 
            width='stretch', 
            key="trade_timeline_chart"
        )
    else:
        st.info("暂无交易记录")

# 页脚
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>股票操作反思系统 | 记录成长，持续改进</div>", 
    unsafe_allow_html=True
)

