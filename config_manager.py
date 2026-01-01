"""
配置管理模块 - 保存和加载用户配置
"""
import json
import os
from typing import Optional


CONFIG_FILE = "app_config.json"


def load_config() -> dict:
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置失败: {e}")
            return {}
    return {}


def save_config(config: dict):
    """保存配置文件"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存配置失败: {e}")


def get_tushare_token() -> Optional[str]:
    """获取保存的 tushare token"""
    config = load_config()
    return config.get('tushare_token', None)


def save_tushare_token(token: str):
    """保存 tushare token"""
    config = load_config()
    config['tushare_token'] = token
    save_config(config)

