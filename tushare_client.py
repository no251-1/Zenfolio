"""
tushare API 封装模块
"""
import tushare as ts
from typing import Optional, Dict
import pandas as pd


class TushareClient:
    """tushare API 客户端封装"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.pro = None
        if token:
            self.set_token(token)
    
    def set_token(self, token: str):
        """设置 tushare token"""
        self.token = token
        ts.set_token(token)
        self.pro = ts.pro_api()
    
    def is_configured(self) -> bool:
        """检查是否已配置 token"""
        return self.pro is not None
    
    def get_stock_basic_info(self, stock_code: str) -> Optional[Dict]:
        """
        获取股票基本信息
        参数: stock_code - 股票代码，如 '000001' 或 '000001.SZ'
        返回: 包含股票名称、代码等信息的字典
        """
        if not self.is_configured():
            return None
        
        try:
            # 处理股票代码格式
            code = stock_code.replace('.', '')
            if len(code) == 6:
                # 判断是上交所还是深交所
                if code.startswith('6'):
                    ts_code = f"{code}.SH"
                else:
                    ts_code = f"{code}.SZ"
            else:
                ts_code = stock_code
            
            # 获取股票基本信息
            df = self.pro.stock_basic(
                exchange='',
                list_status='L',
                fields='ts_code,symbol,name,area,industry,list_date'
            )
            
            # 查找匹配的股票
            stock_info = df[df['ts_code'] == ts_code]
            if stock_info.empty:
                # 尝试用 symbol 查找
                stock_info = df[df['symbol'] == code]
            
            if not stock_info.empty:
                row = stock_info.iloc[0]
                return {
                    'ts_code': row['ts_code'],
                    'symbol': row['symbol'],
                    'name': row['name'],
                    'area': row.get('area', ''),
                    'industry': row.get('industry', ''),
                    'list_date': row.get('list_date', '')
                }
            return None
        except Exception as e:
            print(f"获取股票信息失败: {e}")
            return None
    
    def get_stock_daily(self, stock_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        获取股票日线数据
        参数:
            stock_code - 股票代码
            start_date - 开始日期，格式 'YYYYMMDD'
            end_date - 结束日期，格式 'YYYYMMDD'
        返回: DataFrame 包含日期、开盘、收盘、最高、最低等数据
        """
        if not self.is_configured():
            return None
        
        try:
            # 处理股票代码格式
            code = stock_code.replace('.', '')
            if len(code) == 6:
                if code.startswith('6'):
                    ts_code = f"{code}.SH"
                else:
                    ts_code = f"{code}.SZ"
            else:
                ts_code = stock_code
            
            # 获取日线数据
            df = self.pro.daily(
                ts_code=ts_code,
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', '')
            )
            
            if df is not None and not df.empty:
                # 转换日期格式
                df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
                df = df.sort_values('trade_date')
            
            return df
        except Exception as e:
            print(f"获取股票日线数据失败: {e}")
            return None
    
    def get_realtime_quote(self, stock_code: str) -> Optional[Dict]:
        """
        获取股票实时行情（需要权限）
        参数: stock_code - 股票代码
        返回: 包含当前价格的字典
        """
        if not self.is_configured():
            return None
        
        try:
            # 处理股票代码格式
            code = stock_code.replace('.', '')
            if len(code) == 6:
                if code.startswith('6'):
                    ts_code = f"{code}.SH"
                else:
                    ts_code = f"{code}.SZ"
            else:
                ts_code = stock_code
            
            # 获取实时行情（需要相应权限）
            df = self.pro.daily(ts_code=ts_code, limit=1)
            
            if df is not None and not df.empty:
                latest = df.iloc[0]
                return {
                    'ts_code': ts_code,
                    'close': latest['close'],
                    'open': latest['open'],
                    'high': latest['high'],
                    'low': latest['low'],
                    'vol': latest['vol'],
                    'amount': latest['amount']
                }
            return None
        except Exception as e:
            print(f"获取实时行情失败: {e}")
            return None

