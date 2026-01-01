"""
SQLite 数据库操作模块
"""
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict
import pandas as pd
from models import Trade, Score


class Database:
    """数据库管理类"""
    
    def __init__(self, db_path: str = "stock_reflection.db"):
        self.db_path = db_path
        self.init_database()
        self.migrate_database()  # 迁移旧数据
    
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """初始化数据库表结构"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 创建交易记录表（新结构）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_group_id INTEGER,
                stock_code TEXT NOT NULL,
                stock_name TEXT,
                action_type TEXT NOT NULL,
                trade_type TEXT NOT NULL,
                buy_date TEXT NOT NULL,
                sell_date TEXT,
                buy_price REAL NOT NULL,
                sell_price REAL,
                quantity INTEGER NOT NULL,
                status TEXT DEFAULT '进行中',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建评分记录表（新结构）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scores_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id INTEGER,
                date TEXT NOT NULL,
                action_type TEXT NOT NULL,
                score_type TEXT NOT NULL,
                score INTEGER NOT NULL,
                answer TEXT,
                reflection TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (trade_id) REFERENCES trades_new(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def migrate_database(self):
        """迁移旧数据库结构到新结构"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 检查旧表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='trades' AND name!='trades_new'
        """)
        old_trades_exists = cursor.fetchone() is not None
        
        if old_trades_exists:
            # 迁移旧数据（如果存在）
            try:
                cursor.execute("""
                    INSERT INTO trades_new 
                    (trade_group_id, stock_code, stock_name, action_type, trade_type, 
                     buy_date, buy_price, quantity, status, notes)
                    SELECT 
                        id, stock_code, stock_name, action_type, '买入',
                        date, price, quantity, '已结束', notes
                    FROM trades
                """)
                
                cursor.execute("""
                    INSERT INTO scores_new 
                    (trade_id, date, action_type, score_type, score, answer, reflection)
                    SELECT 
                        (SELECT id FROM trades_new WHERE trade_group_id = s.date LIMIT 1),
                        date, action_type, '主观评分', score, answer, reflection
                    FROM scores s
                """)
                
                conn.commit()
            except Exception as e:
                print(f"数据迁移警告: {e}")
        
        conn.close()
    
    def add_trade(self, trade: Trade) -> int:
        """添加交易记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 如果是买入，创建新的交易组
        if trade.trade_type == "买入":
            # 获取下一个交易组ID
            cursor.execute("SELECT COALESCE(MAX(trade_group_id), 0) + 1 FROM trades_new")
            trade_group_id = cursor.fetchone()[0]
        else:
            trade_group_id = trade.trade_group_id
        
        cursor.execute("""
            INSERT INTO trades_new 
            (trade_group_id, stock_code, stock_name, action_type, trade_type,
             buy_date, sell_date, buy_price, sell_price, quantity, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_group_id,
            trade.stock_code,
            trade.stock_name,
            trade.action_type,
            trade.trade_type,
            trade.buy_date or datetime.now().strftime("%Y-%m-%d"),
            trade.sell_date,
            trade.buy_price,
            trade.sell_price,
            trade.quantity,
            trade.status,
            trade.notes
        ))
        
        trade_id = cursor.lastrowid
        
        # 如果是卖出，更新对应的买入记录状态
        if trade.trade_type == "卖出" and trade_group_id:
            cursor.execute("""
                UPDATE trades_new 
                SET status = '已结束', sell_date = ?, sell_price = ?
                WHERE trade_group_id = ? AND trade_type = '买入'
            """, (trade.sell_date, trade.sell_price, trade_group_id))
        
        conn.commit()
        conn.close()
        return trade_id
    
    def add_score(self, score: Score) -> int:
        """添加评分记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO scores_new 
            (trade_id, date, action_type, score_type, score, answer, reflection)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            score.trade_id,
            score.date or datetime.now().strftime("%Y-%m-%d"),
            score.action_type,
            score.score_type,
            score.score,
            score.answer,
            score.reflection
        ))
        
        score_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return score_id
    
    def get_trade_by_id(self, trade_id: int) -> Optional[Dict]:
        """根据ID获取交易记录"""
        conn = self.get_connection()
        query = "SELECT * FROM trades_new WHERE id = ?"
        df = pd.read_sql_query(query, conn, params=(trade_id,))
        conn.close()
        if not df.empty:
            return df.iloc[0].to_dict()
        return None
    
    def get_active_trades(self) -> List[Dict]:
        """获取所有进行中的交易"""
        conn = self.get_connection()
        query = """
            SELECT * FROM trades_new 
            WHERE status = '进行中' AND trade_type = '买入'
            ORDER BY buy_date DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.to_dict('records')
    
    def get_sold_quantity(self, trade_group_id: int) -> int:
        """获取某个买入交易已卖出的总数量"""
        conn = self.get_connection()
        query = """
            SELECT COALESCE(SUM(quantity), 0) as total_sold
            FROM trades_new
            WHERE trade_group_id = ? AND trade_type = '卖出'
        """
        cursor = conn.cursor()
        cursor.execute(query, (trade_group_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0
    
    def get_all_trades(self, limit: Optional[int] = None) -> List[Dict]:
        """获取所有交易记录（按交易组）"""
        conn = self.get_connection()
        
        query = """
            SELECT * FROM trades_new 
            ORDER BY buy_date DESC, created_at DESC
        """
        if limit:
            query += f" LIMIT {limit}"
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.to_dict('records')
    
    def get_trade_groups(self) -> List[Dict]:
        """获取所有交易组（买入+卖出）"""
        conn = self.get_connection()
        
        query = """
            SELECT 
                trade_group_id,
                stock_code,
                stock_name,
                action_type,
                buy_date,
                sell_date,
                buy_price,
                sell_price,
                quantity,
                status,
                COUNT(*) as trade_count
            FROM trades_new
            WHERE trade_type = '买入'
            GROUP BY trade_group_id, stock_code, stock_name, action_type, buy_date, sell_date, buy_price, sell_price, quantity, status
            ORDER BY buy_date DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.to_dict('records')
    
    def get_scores_by_trade(self, trade_id: int) -> List[Dict]:
        """获取指定交易的所有评分"""
        conn = self.get_connection()
        query = """
            SELECT * FROM scores_new 
            WHERE trade_id = ?
            ORDER BY score_type, date DESC
        """
        df = pd.read_sql_query(query, conn, params=(trade_id,))
        conn.close()
        return df.to_dict('records')
    
    def get_all_scores(self, limit: Optional[int] = None, score_type: Optional[str] = None) -> List[Dict]:
        """获取所有评分记录"""
        conn = self.get_connection()
        
        query = "SELECT * FROM scores_new WHERE 1=1"
        params = []
        
        if score_type:
            query += " AND score_type = ?"
            params.append(score_type)
        
        query += " ORDER BY date DESC, created_at DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        df = pd.read_sql_query(query, conn, params=params if params else None)
        conn.close()
        return df.to_dict('records')
    
    def get_scores_by_date_range(self, start_date: str, end_date: str, score_type: Optional[str] = None) -> pd.DataFrame:
        """按日期范围获取评分记录"""
        conn = self.get_connection()
        
        query = """
            SELECT date, action_type, score_type, score, answer, reflection
            FROM scores_new
            WHERE date >= ? AND date <= ?
        """
        params = [start_date, end_date]
        
        if score_type:
            query += " AND score_type = ?"
            params.append(score_type)
        
        query += " ORDER BY date ASC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    
    def get_scores_summary(self, score_type: Optional[str] = None) -> pd.DataFrame:
        """获取评分汇总统计"""
        conn = self.get_connection()
        
        query = """
            SELECT 
                action_type,
                COUNT(*) as count,
                AVG(score) as avg_score,
                MIN(score) as min_score,
                MAX(score) as max_score
            FROM scores_new
            WHERE 1=1
        """
        params = []
        
        if score_type:
            query += " AND score_type = ?"
            params.append(score_type)
        
        query += " GROUP BY action_type"
        
        df = pd.read_sql_query(query, conn, params=params if params else None)
        conn.close()
        return df
    
    def get_trades_by_stock(self, stock_code: str) -> List[Dict]:
        """根据股票代码获取交易记录"""
        conn = self.get_connection()
        query = """
            SELECT * FROM trades_new 
            WHERE stock_code = ? 
            ORDER BY buy_date DESC
        """
        df = pd.read_sql_query(query, conn, params=(stock_code,))
        conn.close()
        return df.to_dict('records')
    
    def update_trade_status(self, trade_group_id: int) -> bool:
        """检查并更新交易状态（如果全部卖出则标记为已结束）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 获取买入数量和已卖出数量
        cursor.execute("""
            SELECT quantity FROM trades_new 
            WHERE trade_group_id = ? AND trade_type = '买入'
        """, (trade_group_id,))
        buy_result = cursor.fetchone()
        
        if not buy_result:
            conn.close()
            return False
        
        buy_quantity = buy_result[0]
        sold_quantity = self.get_sold_quantity(trade_group_id)
        
        # 如果全部卖出，更新状态为已结束
        if sold_quantity >= buy_quantity:
            cursor.execute("""
                UPDATE trades_new 
                SET status = '已结束'
                WHERE trade_group_id = ? AND trade_type = '买入'
            """, (trade_group_id,))
            success = cursor.rowcount > 0
        else:
            success = True
        
        conn.commit()
        conn.close()
        return success
    
    def delete_trade(self, trade_id: int) -> bool:
        """删除交易记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM trades_new WHERE id = ?", (trade_id,))
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return success
    
    def delete_score(self, score_id: int) -> bool:
        """删除评分记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM scores_new WHERE id = ?", (score_id,))
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return success
